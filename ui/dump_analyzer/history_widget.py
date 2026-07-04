""""Shows a list of dumps to compare"""

import base64
import datetime
import json
import logging
from dataclasses import dataclass

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (QGridLayout, QHBoxLayout, QLineEdit,
                               QPushButton, QStyle, QToolButton, QVBoxLayout,
                               QWidget)

logger = logging.getLogger(__name__)


class HistoryWidget(QWidget):
    FILE_NAME = "dumps.json"
    dump_selected = Signal(bytes)
    dump_loaded = Signal(bytes)

    @dataclass
    class DumpInfo:
        data: bytes
        name_widget: QLineEdit | None = None
        delete_button: QToolButton | None = None
        load_button: QToolButton | None = None
        compare_button: QToolButton | None = None

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._dumps: dict[str, HistoryWidget.DumpInfo] = {}
        self._currently_selected_dump: HistoryWidget.DumpInfo | None = None
        self._main_layout = QVBoxLayout()
        self._grid_layout = QGridLayout()
        save_button_widget = QWidget(self)
        save_button_layout = QHBoxLayout(save_button_widget)
        save_button_layout.setContentsMargins(0, 0, 0, 0)
        self._save_button = QPushButton("Save", self)
        self._save_button.clicked.connect(self._save_current_data)
        save_button_layout.addStretch(1)
        save_button_layout.addWidget(self._save_button)
        save_button_layout.addStretch(1)
        self._main_layout.addWidget(save_button_widget)
        self._main_layout.addLayout(self._grid_layout)
        self._main_layout.addStretch(1)
        self.setLayout(self._main_layout)

        self._load_history()

    def _fill_layout(self) -> None:
        '''Fill the layout with the dump information.'''
        # Clear the layout
        while self._grid_layout.count() > 0:
            item = self._grid_layout.takeAt(0)
            if item is None:
                continue
            widget = item.widget()
            if widget is not None:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()

        for row, (name, dump) in enumerate(self._dumps.items()):
            dump.name_widget = QLineEdit(name, self)
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
            self._grid_layout.addWidget(dump.name_widget, row, 0)

            dump.delete_button = QToolButton(self)
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
            self._grid_layout.addWidget(dump.delete_button, row, 1)

            dump.load_button = QToolButton(self)
            dump.load_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon))
            dump.load_button.setToolTip("Load")
            def on_load_clicked(*, dump: HistoryWidget.DumpInfo = dump) -> None:
                self.dump_loaded.emit(dump.data)
            dump.load_button.clicked.connect(on_load_clicked)
            self._grid_layout.addWidget(dump.load_button, row, 2)

            dump.compare_button = QToolButton(self)
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
            self._grid_layout.addWidget(dump.compare_button, row, 3)


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
