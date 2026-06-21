'''
SectionListWidget is a widget that displays the details of a SectionList
and allows the user to edit it.
'''

import copy
from copy import deepcopy
from typing import Type

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (QAbstractButton, QHBoxLayout, QLabel,
                               QListWidget, QMenu, QPushButton, QSpinBox,
                               QToolButton, QVBoxLayout, QWidget)

from ui.dump_analyzer.section import Section, SectionList
from ui.dump_analyzer.section_value import SectionValue

from .section_widget import SectionDetailsWidgetBase


class SectionListWidget(SectionDetailsWidgetBase[SectionList]):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._parent: Section | None = None
        self._member_list: QListWidget
        self._size_spin_box: QSpinBox
        self._add_button: QAbstractButton
        self._remove_button: QAbstractButton
        self._up_button: QAbstractButton
        self._down_button: QAbstractButton
        self._sections: list[Section] = []

        self._init_ui()

    def _init_ui(self) -> None:
        '''Initialize the UI components.'''
        monospace_font = self.font()
        monospace_font.setFamily("Courier")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._member_list = QListWidget(self)
        self._member_list.setFont(monospace_font)
        self._member_list.currentRowChanged.connect(self._update_ui)
        layout.addWidget(self._member_list)
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(right_layout)
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Size:", self))
        self._size_spin_box = QSpinBox(self)
        self._size_spin_box.setFont(monospace_font)
        self._size_spin_box.valueChanged.connect(self._on_change)
        size_layout.addWidget(self._size_spin_box)
        size_toggle = HexDecSwitchWidget(self)
        size_toggle.toggle_signal.connect(self._toogle_size_spin_box)
        size_layout.addWidget(size_toggle)
        self._toogle_size_spin_box(True)
        right_layout.addLayout(size_layout)
        self._add_button = QPushButton(self)
        self._add_button.setText("➕ Add Section")
        self._add_button.clicked.connect(self._add_section)
        right_layout.addWidget(self._add_button)
        self._remove_button = QPushButton(self)
        self._remove_button.setText("➖ Remove Section")
        self._remove_button.clicked.connect(self._remove_section)
        right_layout.addWidget(self._remove_button)
        self._up_button = QPushButton(self)
        self._up_button.setText("⬆️ Move Up")
        self._up_button.clicked.connect(self._move_section_up)
        right_layout.addWidget(self._up_button)
        self._down_button = QPushButton(self)
        self._down_button.setText("⬇️ Move Down")
        self._down_button.clicked.connect(self._move_section_down)
        right_layout.addWidget(self._down_button)
        self._update_member_list()

    def save_section(self) -> None:
        '''Save the changes to the section list.'''
        if self.section is None:
            return
        self.section.subsections = self._sections[:]

    def _on_section_change(self) -> None:
        '''Set the displayed section information.'''
        section = self.section
        if section is None:
            self._size_spin_box.setValue(0)
            self._sections = []
        else:
            self._size_spin_box.setMinimum(0)
            self._size_spin_box.setMaximum(section.parent.size if section.parent else 0xFFFF)
            self._size_spin_box.setValue(section.size)
            self._sections = deepcopy(section.children())

        self._update_member_list()
        self._on_change()

    def has_changes(self) -> bool:
        '''Check if there are unsaved changes to the section list.'''
        section = self.section
        if section is None:
            print("No section")
            return False
        if section.size != self._size_spin_box.value():
            print("Size changed")
            return True
        if section.children() != self._sections:
            return True
        return False

    def get_size(self) -> int:
        '''Get the size of the section being edited.'''
        return self._size_spin_box.value()

    def get_errors(self) -> list[str]:
        '''Get a list of errors in the section list.'''
        errors: list[str] = []
        for s in self._sections:
            if s.start < 0 or s.end > self.get_size():
                errors.append(f"Section '{s.name}' is out of bounds.")
        for i in range(len(self._sections)):
            for j in range(i + 1, len(self._sections)):
                if self._sections[i].overlaps_with(self._sections[j]):
                    errors.append(f"Section '{self._sections[i].name}' overlaps with section '{self._sections[j].name}'.")
        return errors

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
        current_section = self.section
        if current_section is None:
            return

        if current_section.size != self._size_spin_box.value():
            changed_section = copy.copy(current_section)
            changed_section.size = self._size_spin_box.value()
            self.data_changed.emit()

    def _add_section(self) -> None:
        # create drop down menu to select the type of section to add
        menu = QMenu(self)
        menu.addAction("Section List", lambda: self._add_section_object(SectionList))
        menu.addAction("Value", lambda: self._add_section_object(SectionValue))
        menu.exec(self._add_button.mapToGlobal(self._add_button.rect().bottomLeft()))

    def _add_section_object(self, section_type: Type[Section]) -> None:
        '''Add a new section of the given type.'''
        current_section = self.section
        if current_section is None:
            return
        number = self._find_free_new_section_number()
        new_section = section_type(name=f"New Section {number}", start=0)
        new_section.start = self._find_free_start(new_section.size)
        self._sections.append(new_section)
        self._update_member_list()
        self.data_changed.emit()

    def _remove_section(self) -> None:
        selected_index = self._member_list.currentRow()
        if selected_index < 0 or selected_index >= len(self._sections):
            return
        del self._sections[selected_index]
        self._update_member_list()
        self.data_changed.emit()

    def _move_section_up(self) -> None:
        selected_index = self._member_list.currentRow()
        if selected_index < 1 or selected_index >= len(self._sections):
            return
        self._swap_neighbor_sections(selected_index - 1)
        self._update_member_list()
        self._member_list.setCurrentRow(selected_index - 1)
        self.data_changed.emit()

    def _move_section_down(self) -> None:
        selected_index = self._member_list.currentRow()
        if selected_index < 0 or selected_index >= len(self._sections) - 1:
            return
        self._swap_neighbor_sections(selected_index)
        self._update_member_list()
        self._member_list.setCurrentRow(selected_index + 1)
        self.data_changed.emit()

    def _swap_neighbor_sections(self, first_idx: int) -> None:
        '''Swap the sections at the given index and the next one.'''
        second_idx = first_idx + 1
        first = self._sections[first_idx]
        second = self._sections[second_idx]
        gap = self._sections[second_idx].start - self._sections[first_idx].end
        second.start = first.start
        first.start = second.end + gap

    def _find_free_start(self, size: int) -> int:
        '''Find a free start index for a new section of the given size.'''
        occupied_ranges = [(s.start, s.end) for s in self._sections]
        if not occupied_ranges:
            return 0
        occupied_ranges.sort()
        if occupied_ranges[-1][1] + size <= self.get_size():
            return occupied_ranges[-1][1]
        current_index = 0
        for start, end in occupied_ranges:
            if current_index + size <= start:
                return current_index
            current_index = end
        return current_index

    def _find_free_new_section_number(self) -> int:
        '''Find a free number for a new section with the name "New Section {number}".'''
        number = 1
        for s in self._sections:
            if s.name.startswith(f"New Section "):
                this_number = s.name.rsplit(" ")[2]
                if this_number.isdigit():
                    number = max(number, int(this_number) + 1)
        return number

    def _update_member_list(self) -> None:
        '''Update the member list display.'''
        current_item = self._member_list.currentItem()
        slection = current_item.text() if current_item else None
        self._member_list.clear()
        self._sections.sort(key=lambda s: s.start)
        for s in self._sections:
            self._member_list.addItem(f"{s.name} (0x{s.start:04X} - 0x{s.end:04X}) ({type(s).type_name()})")
        for i in range(self._member_list.count()):
            if self._member_list.item(i).text() == slection:
                self._member_list.setCurrentRow(i)
                break
        self._update_ui()

    def _update_ui(self) -> None:
        '''Update buttons.'''
        selection = self._member_list.currentRow()
        self._remove_button.setEnabled(selection >= 0)
        self._up_button.setEnabled(selection >= 1)
        self._down_button.setEnabled(selection >= 0 and selection < len(self._sections) - 1)


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
