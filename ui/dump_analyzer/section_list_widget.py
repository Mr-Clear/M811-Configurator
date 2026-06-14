'''
SectionListWidget is a widget that displays the details of a SectionList
and allows the user to edit it.
'''

import copy

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (QFormLayout, QHBoxLayout, QSpinBox, QToolButton,
                               QWidget)

from ui.dump_analyzer.section import Section, SectionList

from .section_widget import SectionDetailsWidgetBase


class SectionListWidget(SectionDetailsWidgetBase[SectionList]):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._section: SectionList | None = None
        self._parent: Section | None = None
        self._size_spin_box: QSpinBox
        self._init_ui()

    def _init_ui(self) -> None:
        '''Initialize the UI components.'''
        monospace_font = self.font()
        monospace_font.setFamily("Courier")
        layout = QFormLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

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


    def set_section(self, section: SectionList | None) -> None:
        '''Set the displayed section information.'''
        self._section = section
        if section is None:
            self._size_spin_box.setValue(0)
        else:
            self._size_spin_box.setMinimum(0)
            self._size_spin_box.setMaximum(section.parent.size if section.parent else 0xFFFF)
            self._size_spin_box.setValue(section.size)

        self._on_change()

    def get_section(self) -> SectionList | None:
        '''Get the currently displayed section.'''
        return self._section

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
        current_section = self.get_section()
        if current_section is None:
            return

        if current_section.size != self._size_spin_box.value():
            changed_section = copy.copy(current_section)
            changed_section.size = self._size_spin_box.value()
            self.data_changed.emit(changed_section)

    def get_size(self) -> int:
        '''Get the size of the section being edited.'''
        return self._size_spin_box.value()


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
