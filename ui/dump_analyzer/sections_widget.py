'''Widget to manage sections.'''

from PySide6.QtCore import QAbstractItemModel, QModelIndex, QObject, Qt
from PySide6.QtWidgets import (QHBoxLayout, QHeaderView, QToolButton,
                               QTreeView, QVBoxLayout, QWidget)

from .section import Section
from .section_list import SectionList
from .section_widget import SectionWidget


class SectionsWidget(QWidget):
    def __init__(self, root: SectionList, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._root = root
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        left_panel = QWidget(self)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        buttons = QWidget(self)
        buttons_layout = QHBoxLayout(buttons)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.addStretch(1)

        self.add_button = QToolButton(self)
        self.add_button.setText("➕")
        self.add_button.clicked.connect(self._add_section)
        buttons_layout.addWidget(self.add_button)

        self.remove_button = QToolButton(self)
        self.remove_button.setText("➖")
        self.remove_button.clicked.connect(self._remove_section)

        buttons_layout.addWidget(self.remove_button)
        left_layout.addWidget(buttons)
        self._tree_view = QTreeView(self)
        self._tree_view.setHeaderHidden(True)
        self._tree_view.setModel(SectionsTreeModel(self._root, self))
        self._tree_view.selectionModel().selectionChanged.connect(self._on_tree_selection_changed)
        self._tree_view.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._tree_view.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self._tree_view.header().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self._tree_view.selectionModel().selectionChanged.connect(self._on_tree_selection_changed)
        self._tree_view.expandAll()
        left_layout.addWidget(self._tree_view)
        layout.addWidget(left_panel)
        self._details_widget = SectionWidget(self)
        layout.addWidget(self._details_widget, 1)
        self._details_widget.section_changed.connect(self._on_section_changed)

        self._tree_view.setCurrentIndex(self._tree_view.model().index(0, 0, QModelIndex()))

    def _on_section_changed(self) -> None:
        '''Handle changes to the section information.'''
        if self._details_widget.section is None:
            return
        self._tree_view.model().layoutChanged.emit()

    def _add_section(self) -> None:
        pass

    def _remove_section(self) -> None:
        '''Remove the currently selected section.'''
        index = self._tree_view.currentIndex()
        if not index.isValid():
            return
        section = index.internalPointer()
        parent_index = self._tree_view.model().parent(index) # type: ignore
        if not parent_index.isValid():
            return
        child = parent_index.internalPointer()
        child.children().remove(section)
        self._tree_view.model().layoutChanged.emit() # type: ignore

    def _on_tree_selection_changed(self) -> None:
        '''Update the details widget when the selection changes.'''
        index = self._tree_view.currentIndex()
        if not index.isValid():
            self._details_widget.set_section(None)
            return
        section = index.internalPointer()
        self._details_widget.set_section(section)

class SectionsTreeModel(QAbstractItemModel):
    def __init__(self, root: Section, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._root = SectionList(name="INVISIBLE_ROOT", start=0, length=0xFFFF, subsections=[root])

    def rowCount(self, parent: QModelIndex) -> int: # type: ignore
        if not parent.isValid():
            return 1
        section = parent.internalPointer()
        return len(section.children())

    def columnCount(self, parent: QModelIndex) -> int: # type: ignore
        return 3

    def index(self, row: int, column: int, parent: QModelIndex) -> QModelIndex: # type: ignore
        if not parent.isValid():
            section = self._root
        else:
            section = parent.internalPointer()
        if 0 <= row < len(section.children()):
            return self.createIndex(row, column, section.children()[row])
        return QModelIndex()

    def parent(self, index: QModelIndex) -> QModelIndex: # type: ignore
        if not index.isValid():
            return QModelIndex()
        section = index.internalPointer()
        if section == self._root:
            return QModelIndex()
        parent_section = self._find_parent(self._root, section)
        if parent_section is None:
            return QModelIndex()
        if parent_section == self._root:
            return self.createIndex(0, 0, self._root)
        grandparent_section = self._find_parent(self._root, parent_section)
        if grandparent_section is None:
            return QModelIndex()
        row = grandparent_section.children().index(parent_section)
        return self.createIndex(row, 0, parent_section)

    def data(self, index: QModelIndex, role: int) -> str | None: # type: ignore
        if not index.isValid():
            return None
        section = index.internalPointer()
        if role == Qt.ItemDataRole.DisplayRole:
            if index.column() == 0:
                return section.name
            if index.column() == 1:
                return f"0x{section.absolute_start:04X}"
            if index.column() == 2:
                return f"0x{section.absolute_end:04X}"
        return None

    def _find_parent(self, current: Section, target: Section) -> Section | None:
        for child in current.children():
            if child == target:
                return current
            parent = self._find_parent(child, target)
            if parent is not None:
                return parent
        return None
