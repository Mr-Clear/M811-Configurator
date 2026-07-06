'''Widget to manage sections.'''

from PySide6.QtCore import (QAbstractItemModel, QModelIndex, QObject, QPoint,
                            Qt, Signal)
from PySide6.QtWidgets import (QHeaderView, QMenu, QSplitter, QTreeView,
                               QVBoxLayout, QWidget)

from .section_widgets.clipboard import copy_section_to_clipboard
from .section_widgets.section_widget import SectionWidget
from .sections.list_section import ListSection
from .sections.section import Section


class SectionsWidget(QWidget):
    sections_changed = Signal()

    def __init__(self, root: ListSection, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._root = root
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        left_panel = QWidget(self)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        self._tree_view = QTreeView(self)
        self._tree_view_model = SectionsTreeModel(self._root, self)
        self._tree_view.setModel(self._tree_view_model)
        self._tree_view.setIndentation(8)
        self._tree_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._tree_view.header().setVisible(True)
        self._tree_view.header().setStretchLastSection(False)
        self._tree_view.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._tree_view.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self._tree_view.header().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self._tree_view.selectionModel().selectionChanged.connect(self._on_tree_selection_changed)
        self._tree_view.customContextMenuRequested.connect(self._show_tree_context_menu)
        self._tree_view.expand(self._tree_view_model.index(0, 0, QModelIndex()))
        left_layout.addWidget(self._tree_view)
        splitter.addWidget(left_panel)
        self._details_widget = SectionWidget(self)
        splitter.addWidget(self._details_widget)
        self._details_widget.section_changed.connect(self._on_section_changed)
        layout.addWidget(splitter)
        self.setLayout(layout)

        self._tree_view.setCurrentIndex(self._tree_view_model.index(0, 0, QModelIndex()))

    def _on_section_changed(self) -> None:
        '''Handle changes to the section information.'''
        if self._details_widget.section is None:
            return
        self._tree_view_model.layoutChanged.emit()
        self.sections_changed.emit()

    def _add_section(self) -> None:
        pass

    def _remove_section(self) -> None:
        '''Remove the currently selected section.'''
        index = self._tree_view.currentIndex()
        if not self._can_remove_index(index):
            return

        row = index.row()
        assert row >= 0
        parent_index = self._tree_view_model.parent(index)
        parent_section = parent_index.internalPointer()
        section = index.internalPointer()
        parent_section.children().remove(section)

        next_index = self._next_index_after_removal(parent_index, row)
        self._tree_view_model.layoutChanged.emit()
        self._tree_view.expand(self._tree_view_model.index(0, 0, QModelIndex()))
        self._tree_view.setCurrentIndex(next_index)
        self.sections_changed.emit()

    def _copy_section(self) -> None:
        '''Copy the currently selected section to the clipboard.'''
        index = self._tree_view.currentIndex()
        if not index.isValid():
            return
        section = index.internalPointer()
        copy_section_to_clipboard(section)

    def _show_tree_context_menu(self, position: QPoint) -> None:
        '''Show the tree context menu for the selected section.'''
        index = self._tree_view.indexAt(position)
        if not index.isValid():
            return

        self._tree_view.setCurrentIndex(index)
        menu = QMenu(self)
        copy_action = menu.addAction("Copy Section")
        delete_action = menu.addAction("Delete Section")
        delete_action.setEnabled(self._can_remove_index(index))

        action = menu.exec(self._tree_view.viewport().mapToGlobal(position))
        if action == copy_action:
            self._copy_section()
        elif action == delete_action:
            self._remove_section()

    def _can_remove_index(self, index: QModelIndex) -> bool:
        '''Check whether the given index can be removed from the tree.'''
        if not index.isValid():
            return False
        parent_index = self._tree_view_model.parent(index)
        if not parent_index.isValid():
            return False
        parent = parent_index.internalPointer()
        if parent == self._tree_view_model.root:
            return False
        return isinstance(parent, ListSection)

    def _next_index_after_removal(self, parent_index: QModelIndex, removed_row: int) -> QModelIndex:
        '''Find the next tree index to select after removing a section.'''
        if not parent_index.isValid():
            return QModelIndex()

        parent_section = parent_index.internalPointer()
        child_count = len(parent_section.children(True))
        if child_count == 0:
            return parent_index
        next_row = min(removed_row, child_count - 1)
        return self._tree_view_model.index(next_row, 0, parent_index)

    def _on_tree_selection_changed(self) -> None:
        '''Update the details widget when the selection changes.'''
        index = self._tree_view.currentIndex()
        if not index.isValid():
            self._details_widget.set_section(None)
            return
        section = index.internalPointer()
        self._details_widget.set_section(section)

    @property
    def root_section(self) -> ListSection:
        '''Get the root section of the section tree.'''
        return self._root
    @root_section.setter
    def root_section(self, value: ListSection) -> None:
        '''Set the root section of the section tree.'''
        self._root = value
        self._tree_view_model.set_root(value)
        self._tree_view.expand(self._tree_view_model.index(0, 0, QModelIndex()))
        self._tree_view.setCurrentIndex(self._tree_view_model.index(0, 0, QModelIndex()))


class SectionsTreeModel(QAbstractItemModel):
    def __init__(self, root: Section, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.set_root(root)

    def set_root(self, root: Section) -> None:
        '''Set the root section of the tree model.'''
        self._root = ListSection(name="INVISIBLE_ROOT", relative_start=0, length=0xFFFF, subsections=[root])
        self.layoutChanged.emit()

    @property
    def root(self) -> ListSection:
        '''Get the invisible root section used by the tree model.'''
        return self._root

    def rowCount(self, parent: QModelIndex) -> int: # type: ignore
        if not parent.isValid():
            return 1
        section = parent.internalPointer()
        return len(section.children(True))

    def columnCount(self, parent: QModelIndex) -> int: # type: ignore
        return 3

    def index(self, row: int, column: int, parent: QModelIndex) -> QModelIndex: # type: ignore
        if not parent.isValid():
            section = self._root
        else:
            section = parent.internalPointer()
        if 0 <= row < len(section.children(True)):
            return self.createIndex(row, column, section.children(True)[row])
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
        row = grandparent_section.children(True).index(parent_section)
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

    def headerData(self, section: int, orientation: Qt.Orientation, role: int) -> str | None: # type: ignore
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation != Qt.Orientation.Horizontal:
            return None
        if section == 0:
            return "Name"
        if section == 1:
            return "Start"
        if section == 2:
            return "End"
        return None

    def _find_parent(self, current: Section, target: Section) -> Section | None:
        for child in current.children(True):
            if child == target:
                return current
            parent = self._find_parent(child, target)
            if parent is not None:
                return parent
        return None
