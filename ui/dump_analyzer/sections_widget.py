'''Widget to manage sections.'''

from PySide6.QtCore import QAbstractItemModel, QModelIndex, QObject, Qt, Signal
from PySide6.QtWidgets import (QFormLayout, QHBoxLayout, QLabel, QLineEdit,
                               QPushButton, QSpinBox, QToolButton, QTreeView,
                               QVBoxLayout, QWidget)

from .section import Section


class SectionsWidget(QWidget):
    def __init__(self, root: Section, parent: QWidget | None = None) -> None:
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
        left_layout.addWidget(self._tree_view)
        layout.addWidget(left_panel)
        self._details_widget = SectionDetailsWidget(self)
        self._details_widget.set_section(root, root)
        layout.addWidget(self._details_widget, 1)
        self._details_widget.section_changed.connect(self._on_section_changed)

    def _on_section_changed(self) -> None:
        '''Handle changes to the section information.'''
        if self._details_widget.section is None:
            return
        self._tree_view.model().layoutChanged.emit()

    def _add_section(self) -> None:
        '''Add a new section as a child of the currently selected section.'''
        index = self._tree_view.currentIndex()
        if not index.isValid():
            parent_section = self._root
        else:
            parent_section = index.internalPointer()
        new_section = Section(name="New Section", start=parent_section.start, size=parent_section.size)
        try:
            parent_section.add_section(new_section)
            self._tree_view.model().layoutChanged.emit() # type: ignore
        except ValueError as e:
            print(f"Failed to add section: {e}")

    def _remove_section(self) -> None:
        '''Remove the currently selected section.'''
        index = self._tree_view.currentIndex()
        if not index.isValid():
            return
        section = index.internalPointer()
        parent_index = self._tree_view.model().parent(index) # type: ignore
        if not parent_index.isValid():
            return
        parent_section = parent_index.internalPointer()
        parent_section.subsections.remove(section)
        self._tree_view.model().layoutChanged.emit() # type: ignore

    def _on_tree_selection_changed(self) -> None:
        '''Update the details widget when the selection changes.'''
        index = self._tree_view.currentIndex()
        if not index.isValid():
            self._details_widget.set_section(None, None)
            return
        section = index.internalPointer()
        parent_index = self._tree_view.model().parent(index) # type: ignore
        parent_section = parent_index.internalPointer() if parent_index.isValid() else None
        self._details_widget.set_section(section, parent_section)

class SectionsTreeModel(QAbstractItemModel):
    def __init__(self, root: Section, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._root = root

    def rowCount(self, parent: QModelIndex) -> int: # type: ignore
        if not parent.isValid():
            return 1
        section = parent.internalPointer()
        return len(section.subsections)

    def columnCount(self, parent: QModelIndex) -> int: # type: ignore
        return 1

    def index(self, row: int, column: int, parent: QModelIndex) -> QModelIndex: # type: ignore
        if not parent.isValid():
            section = self._root
        else:
            section = parent.internalPointer()
        if 0 <= row < len(section.subsections):
            return self.createIndex(row, column, section.subsections[row])
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
        row = grandparent_section.subsections.index(parent_section)
        return self.createIndex(row, 0, parent_section)

    def data(self, index: QModelIndex, role: int) -> str | None: # type: ignore
        if not index.isValid():
            return None
        section = index.internalPointer()
        if role == Qt.ItemDataRole.DisplayRole:
            return f"{section.name} (0x{section.start:X} - 0x{section.end:X})"
        return None

    def _find_parent(self, current: Section, target: Section) -> Section | None:
        for subsection in current.subsections:
            if subsection == target:
                return current
            parent = self._find_parent(subsection, target)
            if parent is not None:
                return parent
        return None


class SectionDetailsWidget(QWidget):
    section_changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._section: Section | None = None
        self._parent: Section | None = None
        self._name_text: QLineEdit
        self._start_spin_box: QSpinBox
        self._size_spin_box: QSpinBox
        self._color_text: QLineEdit
        self._end_label: QLabel
        self._error_label: QLabel
        self._save_button: QPushButton
        self.discard_button: QPushButton
        self._end_is_hex = True
        self._init_ui()

    def _init_ui(self) -> None:
        '''Initialize the UI components.'''
        monospace_font = self.font()
        monospace_font.setFamily("Courier")
        layout = QFormLayout(self)
        self._name_text = QLineEdit(self)
        self._name_text.textChanged.connect(self._on_change)
        layout.addRow("Name:", self._name_text)

        start_layout = QHBoxLayout()
        self._start_spin_box = QSpinBox(self)
        self._start_spin_box.setFont(monospace_font)
        self._start_spin_box.valueChanged.connect(self._on_change)
        start_layout.addWidget(self._start_spin_box)
        start_toggle = HexDecSwitchWidget(self)
        start_toggle.toggle_signal.connect(self._toogle_start_spin_box)
        start_layout.addWidget(start_toggle)
        self._toogle_start_spin_box(True)
        layout.addRow("Start:", start_layout)

        size_layout = QHBoxLayout()
        self._size_spin_box = QSpinBox(self)
        self._size_spin_box.setFont(monospace_font)
        self._size_spin_box.valueChanged.connect(self._on_change)
        size_layout.addWidget(self._size_spin_box)
        size_toggle = HexDecSwitchWidget(self)
        size_toggle.toggle_signal.connect(self._toogle_size_spin_box)
        size_layout.addWidget(size_toggle)
        self._toogle_size_spin_box(True)
        layout.addRow("Size:", size_layout)

        end_layout = QHBoxLayout()
        self._end_label = QLabel(self)
        self._end_label.setFont(monospace_font)
        self._end_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._end_label.setFrameStyle(QLabel.Shape.Panel | QLabel.Shadow.Raised)
        end_layout.addWidget(self._end_label)
        end_toggle = HexDecSwitchWidget(self)
        end_toggle.toggle_signal.connect(self._toogle_end_label)
        end_layout.addWidget(end_toggle)
        layout.addRow("End:", end_layout)

        self._color_text = QLineEdit(self)
        self._color_text.textChanged.connect(self._on_change)
        layout.addRow("Color:", self._color_text)

        buttons = QWidget(self)
        buttons_layout = QHBoxLayout(buttons)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.addStretch(1)
        self._error_label = QLabel(self)
        self._error_label.setStyleSheet("color: red")
        buttons_layout.addWidget(self._error_label)
        self._save_button = QPushButton("Save", self)
        self._save_button.clicked.connect(self._on_save)
        buttons_layout.addWidget(self._save_button)
        self._discard_button = QPushButton("Discard", self)
        self._discard_button.clicked.connect(self._on_discard)
        buttons_layout.addWidget(self._discard_button)
        layout.addRow(buttons)

    def set_section(self, section: Section | None, parent: Section | None) -> None:
        '''Set the displayed section information.'''
        self._section = section
        self._parent = parent
        if section is None:
            self._name_text.setText("")
            self._start_spin_box.setValue(0)
            self._size_spin_box.setValue(0)
            self._color_text.setText("")
            self._end_label.setText("")
            enabled = False
        else:
            self._name_text.setText(f"{section.name}")
            self._start_spin_box.setValue(section.start)
            self._start_spin_box.setMinimum(parent.start if parent else 0)
            self._start_spin_box.setMaximum(parent.end - 1 if parent else 0xFFFF)
            self._size_spin_box.setValue(section.size)
            self._size_spin_box.setMinimum(0)
            self._size_spin_box.setMaximum(parent.size if parent else 0xFFFF)
            color_text = section.color.name() if section.color else "None"
            self._color_text.setText(f"{color_text}")
            if self._end_is_hex:
                self._end_label.setText(f"0x{section.end:X}")
            else:
                self._end_label.setText(f"{section.end}")
            enabled = section != parent

        self._name_text.setEnabled(enabled)
        self._start_spin_box.setEnabled(enabled)
        self._size_spin_box.setEnabled(enabled)
        self._color_text.setEnabled(enabled)

        self._on_change()

    @property
    def section(self) -> Section | None:
        '''Get the currently displayed section.'''
        return self._section

    def _toogle_start_spin_box(self, is_hex: bool) -> None:
        '''Toggle the start text between hex and decimal.'''
        if is_hex:
            self._start_spin_box.setPrefix("0x")
            self._start_spin_box.setDisplayIntegerBase(16)
        else:
            self._start_spin_box.setPrefix("")
            self._start_spin_box.setDisplayIntegerBase(10)

    def _toogle_size_spin_box(self, is_hex: bool) -> None:
        '''Toggle the end text between hex and decimal.'''
        if is_hex:
            self._size_spin_box.setPrefix("0x")
            self._size_spin_box.setDisplayIntegerBase(16)
        else:
            self._size_spin_box.setPrefix("")
            self._size_spin_box.setDisplayIntegerBase(10)

    def _toogle_end_label(self, is_hex: bool) -> None:
        '''Toggle the end text between hex and decimal.'''
        self._end_is_hex = is_hex
        self._on_change()

    def _on_change(self) -> None:
        '''Handle changes to the section information.'''
        change = False
        error = ''
        if self._section is None or self._parent is None:
            change = False
        else:
            name = self._name_text.text()
            start = int(self._start_spin_box.text(), 16)
            size = self._size_spin_box.value()
            color_text = self._color_text.text()
            self._end_label.setText(f"0x{start + size:X}")
            s = self._section
            if s.name != name or s.start != start or s.size != size:
                if start < self._parent.start or start + size > self._parent.end:
                    error = "Section is out of bounds of parent section."
                else:
                    overlaps = self._parent.get_overlaps(start, size)
                    if overlaps and (len(overlaps) == 1 and overlaps[0] != self._section):
                        error = "Section overlaps with existing sibling sections."
                change = True
            else:
                change = False
        self._save_button.setEnabled(change and not error)
        self._discard_button.setEnabled(change)
        self._error_label.setText(error)
        self._error_label.setEnabled(len(error) > 0)

    def _on_save(self) -> None:
        '''Save the changes to the section.'''
        if self._section is None:
            return
        self._section.name = self._name_text.text()
        self._section.start = int(self._start_spin_box.text(), 16)
        self._section.size = self._size_spin_box.value()
        self.section_changed.emit()
        self._on_change()

    def _on_discard(self) -> None:
        '''Discard the changes to the section.'''
        if self._section is None:
            return
        self.set_section(self._section, self._parent)

class HexDecSwitchWidget(QToolButton):
    toggle_signal = Signal(bool)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._is_hex = False
        self.toggle()
        self.clicked.connect(self.toggle)

    def is_hex(self) -> bool:
        return self._is_hex

    def toggle(self) -> None:
        self._is_hex = not self._is_hex
        self.setText("Hex" if self._is_hex else "Dec")
        self.toggle_signal.emit(self._is_hex)
