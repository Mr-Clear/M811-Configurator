""""Shows a list of dumps to compare"""

import base64
import datetime
import json
import logging
from dataclasses import dataclass

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QDrag, QDropEvent, QMouseEvent, QPixmap
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QLineEdit,
                               QListWidget, QListWidgetItem, QPushButton,
                               QStyle, QToolButton, QVBoxLayout, QWidget)

logger = logging.getLogger(__name__)


class DragHandleLabel(QLabel):
    def __init__(self, list_widget: 'HistoryListWidget', item: QListWidgetItem, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._list_widget = list_widget
        self._item = item
        self._press_position: QPoint | None = None
        self.setText('☰')
        self.setToolTip('Drag to reorder')
        self.setCursor(Qt.CursorShape.OpenHandCursor)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._press_position = event.position().toPoint()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            self._list_widget.setCurrentItem(self._item)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if event.buttons() & Qt.MouseButton.LeftButton and self._press_position is not None:
            if (event.position().toPoint() - self._press_position).manhattanLength() >= self._list_widget.drag_start_distance():
                self._press_position = None
                self._list_widget.start_drag_for_item(self._item)
                return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._press_position = None
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        super().mouseReleaseEvent(event)


class HistoryListWidget(QListWidget):
    order_changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setSelectionMode(QListWidget.SelectionMode.SingleSelection)

    def drag_start_distance(self) -> int:
        return QApplication.startDragDistance()

    def start_drag_for_item(self, item: QListWidgetItem) -> None:
        self.setCurrentItem(item)
        self.startDrag(Qt.DropAction.MoveAction)

    def startDrag(self, supported_actions: Qt.DropAction) -> None:
        indexes = self.selectedIndexes()
        if not indexes:
            return

        mime_data = self.model().mimeData(indexes)

        drag = QDrag(self)
        drag.setMimeData(mime_data)

        transparent_pixmap = QPixmap(1, 1)
        transparent_pixmap.fill(Qt.GlobalColor.transparent)
        drag.setPixmap(transparent_pixmap)
        drag.setHotSpot(QPoint())

        drag.exec(supported_actions, self.defaultDropAction())

    def dropEvent(self, event: QDropEvent) -> None:
        super().dropEvent(event)
        self.order_changed.emit()


class HistoryWidget(QWidget):
    FILE_NAME = "dumps.json"
    dump_selected = Signal(bytes)
    dump_loaded = Signal(bytes)

    @dataclass
    class DumpInfo:
        data: bytes
        name_widget: QLineEdit | None = None
        list_item: QListWidgetItem | None = None
        delete_button: QToolButton | None = None
        load_button: QToolButton | None = None
        compare_button: QToolButton | None = None

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._dumps: dict[str, HistoryWidget.DumpInfo] = {}
        self._currently_selected_dump: HistoryWidget.DumpInfo | None = None
        self._main_layout = QVBoxLayout()
        self._history_list = HistoryListWidget(self)
        self._history_list.order_changed.connect(self._sync_order_from_list)
        save_button_widget = QWidget(self)
        save_button_layout = QHBoxLayout(save_button_widget)
        save_button_layout.setContentsMargins(0, 0, 0, 0)
        self._save_button = QPushButton("Save", self)
        self._save_button.clicked.connect(self._save_current_data)
        save_button_layout.addStretch(1)
        save_button_layout.addWidget(self._save_button)
        save_button_layout.addStretch(1)
        self._main_layout.addWidget(save_button_widget)
        self._main_layout.addWidget(self._history_list)
        self.setLayout(self._main_layout)

        self._load_history()

    def _fill_layout(self) -> None:
        '''Fill the layout with the dump information.'''
        self._history_list.clear()

        for name, dump in self._dumps.items():
            item = QListWidgetItem(self._history_list)
            row_widget = QWidget(self._history_list)
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(4, 2, 4, 2)
            row_layout.setSpacing(6)

            dump.list_item = item
            drag_handle = DragHandleLabel(self._history_list, item, row_widget)
            row_layout.addWidget(drag_handle)

            dump.name_widget = QLineEdit(name, row_widget)
            def on_name_changed(*, name_widget: QLineEdit = dump.name_widget, old_name: str = name) -> None:
                text = name_widget.text()
                if text == old_name:
                    return
                if text in self._dumps:
                    logger.warning(f"Rename requested to existing dump name '{text}'")
                    name_widget.setText(old_name)
                    return

                renamed_dumps: dict[str, HistoryWidget.DumpInfo] = {}
                for current_name, current_dump in self._dumps.items():
                    if current_name == old_name:
                        renamed_dumps[text] = current_dump
                    else:
                        renamed_dumps[current_name] = current_dump

                self._dumps = renamed_dumps
                self._save_history()
                self._fill_layout()

            dump.name_widget.editingFinished.connect(on_name_changed)
            row_layout.addWidget(dump.name_widget, 1)

            dump.delete_button = QToolButton(row_widget)
            dump.delete_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon))
            dump.delete_button.setToolTip("Delete")
            def on_delete_clicked(*, name: str = name) -> None:
                logger.info(f"Deleting dump {name}")
                removed_dump = self._dumps.pop(name, None)
                if removed_dump is None:
                    logger.warning(f"Delete requested for missing dump '{name}'")
                    return
                if self._currently_selected_dump is removed_dump:
                    self._currently_selected_dump = None
                self._save_history()
                self._fill_layout()
            dump.delete_button.clicked.connect(on_delete_clicked)
            row_layout.addWidget(dump.delete_button)

            dump.load_button = QToolButton(row_widget)
            dump.load_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon))
            dump.load_button.setToolTip("Load")
            def on_load_clicked(*, dump: HistoryWidget.DumpInfo = dump) -> None:
                self.dump_loaded.emit(dump.data)
            dump.load_button.clicked.connect(on_load_clicked)
            row_layout.addWidget(dump.load_button)

            dump.compare_button = QToolButton(row_widget)
            dump.compare_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogContentsView))
            dump.compare_button.setToolTip("Compare")
            dump.compare_button.setCheckable(True)
            dump.compare_button.setChecked(self._currently_selected_dump == dump)
            def on_compare_clicked(*, dump: HistoryWidget.DumpInfo = dump) -> None:
                if self._currently_selected_dump is not None and self._currently_selected_dump.compare_button:
                    self._currently_selected_dump.compare_button.setChecked(False)
                self._currently_selected_dump = dump
                self.dump_selected.emit(dump.data)
            dump.compare_button.clicked.connect(on_compare_clicked)
            row_layout.addWidget(dump.compare_button)

            item.setSizeHint(row_widget.sizeHint())
            self._history_list.addItem(item)
            self._history_list.setItemWidget(item, row_widget)

    def _sync_order_from_list(self) -> None:
        ordered_names: list[str] = []
        for row in range(self._history_list.count()):
            item = self._history_list.item(row)
            for name, dump in self._dumps.items():
                if dump.list_item is item:
                    ordered_names.append(name)
                    break

        if len(ordered_names) != len(self._dumps):
            logger.warning('Failed to resolve all dump names after reorder')
            self._fill_layout()
            return

        self._dumps = {name: self._dumps[name] for name in ordered_names}
        self._save_history()


    def _load_history(self) -> None:
        '''Load the history of dumps to compare.'''
        try:
            j = json.load(open(self.FILE_NAME, "r"))
            self._dumps = {name: HistoryWidget.DumpInfo(base64.b64decode(data)) for name, data in j.items()}
        except FileNotFoundError:
            self._dumps = {}
        self._fill_layout()

    def _save_history(self) -> None:
        '''Save the history of dumps to compare.'''
        logger.debug(f"Saving {len(self._dumps)} dumps to {self.FILE_NAME}")
        dumps = {name: base64.b64encode(dump.data).decode("utf-8") for name, dump in self._dumps.items()}
        json.dump(dumps, open(self.FILE_NAME, "w"), indent=4)

    def _save_current_data(self) -> None:
        '''Save the current data to the history of dumps to compare.'''
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.add_dump(f"{timestamp}", b'')

    def add_dump(self, name: str, data: bytes) -> None:
        '''Add a dump to the history of dumps to compare.'''
        self._dumps[name] = HistoryWidget.DumpInfo(data)
        self._fill_layout()
        self._save_history()
