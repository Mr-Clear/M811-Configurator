'''Widget for displaying and editing a Section.'''

from __future__ import annotations

from abc import abstractmethod
from typing import Generic, TypeVar

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFontMetrics
from PySide6.QtWidgets import (QColorDialog, QHBoxLayout, QLabel, QLineEdit,
                               QPushButton, QSpinBox, QToolButton, QVBoxLayout,
                               QWidget)

from ui.dump_analyzer.section_widgets.section_types import get_section_types

from ..sections.section import Section


def _editor_for_type(section_type: type[Section]) -> type[SectionDetailsWidgetBase[Section]]:
    '''Get the editor widget type for the given section type.'''
    if section_type in get_section_types():
        return get_section_types()[section_type]
    raise ValueError(f"Unknown section type: {section_type}")

class SectionWidget(QWidget):
    section_changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._section: Section | None = None
        self._name_text: QLineEdit
        self._start_spin_box: QSpinBox
        self._size_label: QLabel
        self._color_label: QLabel
        self._end_label: QLabel
        self._save_button: QPushButton
        self._discard_button: QPushButton
        self._section_editor_container: QWidget
        self._section_editor: SectionDetailsWidgetBase[Section] | None = None
        self._size_is_hex = True
        self._end_is_hex = True
        self._current_color: QColor | None = None
        self._init_ui()

    def _init_ui(self) -> None:
        '''Initialize the UI components.'''
        monospace_font = self.font()
        monospace_font.setFamily("Courier")
        main_layout = QVBoxLayout(self)

        # Col 1: Name and color
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel("Name:", self))
        self._name_text = QLineEdit(self)
        self._name_text.textChanged.connect(self._on_change)
        layout.addWidget(self._name_text)
        layout.addSpacing(8)
        layout.addWidget(QLabel("Color:", self))
        self._color_label = QLabel(self)
        self._color_label.setFont(monospace_font)
        self._color_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._color_label.setFrameStyle(QLabel.Shape.Panel | QLabel.Shadow.Raised)
        self._color_label.setStyleSheet('background-color: transparent')
        self._color_label.setMinimumWidth(QFontMetrics(self._color_label.font()).horizontalAdvance("0xFFFFFF00"))
        layout.addWidget(self._color_label)
        self._color_button = QToolButton(self)
        self._color_button.setText("...")
        self._color_button.clicked.connect(self._on_color_button_clicked)
        layout.addWidget(self._color_button)
        main_layout.addLayout(layout)

        # Col 2: Start, size and end
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        # Start
        layout.addWidget(QLabel("Start:", self))
        self._start_spin_box = QSpinBox(self)
        self._start_spin_box.setFont(monospace_font)
        self._start_spin_box.valueChanged.connect(self._on_change)
        layout.addWidget(self._start_spin_box)
        start_toggle = HexDecSwitchWidget(self)
        start_toggle.toggle_signal.connect(self._toogle_start_spin_box)
        layout.addWidget(start_toggle)
        self._toogle_start_spin_box(True)
        # Size
        layout.addSpacing(8)
        layout.addWidget(QLabel("Size:", self))
        self._size_label = QLabel(self)
        self._size_label.setFont(monospace_font)
        self._size_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._size_label.setFrameStyle(QLabel.Shape.Panel | QLabel.Shadow.Raised)
        layout.addWidget(self._size_label)
        size_toggle = HexDecSwitchWidget(self)
        size_toggle.toggle_signal.connect(self._toogle_size_spin_box)
        layout.addWidget(size_toggle)
        # End
        layout.addSpacing(8)
        layout.addWidget(QLabel("End:", self))
        self._end_label = QLabel(self)
        self._end_label.setFont(monospace_font)
        self._end_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._end_label.setFrameStyle(QLabel.Shape.Panel | QLabel.Shadow.Raised)
        layout.addWidget(self._end_label)
        end_toggle = HexDecSwitchWidget(self)
        end_toggle.toggle_signal.connect(self._toogle_end_label)
        layout.addWidget(end_toggle)
        main_layout.addLayout(layout)

        # Col 3: Type dependent widget
        self._section_editor_container = QWidget(self)
        section_editor_container_layout = QVBoxLayout(self._section_editor_container)
        section_editor_container_layout.setContentsMargins(0, 0, 0, 0)
        self._section_editor_container.setLayout(section_editor_container_layout)
        main_layout.addWidget(self._section_editor_container, 1)

        main_layout.addStretch(1)

        # Col 4: Buttons and error message
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch(1)
        self._error_label = QLabel(self)
        self._error_label.setStyleSheet("color: red")
        layout.addWidget(self._error_label)
        self._save_button = QPushButton("Save", self)
        self._save_button.clicked.connect(self._on_save)
        layout.addWidget(self._save_button)
        self._discard_button = QPushButton("Discard", self)
        self._discard_button.clicked.connect(self._on_discard)
        layout.addWidget(self._discard_button)
        main_layout.addLayout(layout)

        self._toogle_size_spin_box(True)

    def set_section(self, section: Section | None) -> None:
        '''Set the displayed section information.'''
        self._section = section
        self.fill_data(section)
        self._on_change()

    def fill_data(self, section: Section | None) -> None:
        '''Fill the ui with the given section information.'''

        if section is None:
            self._name_text.setText("")
            self._start_spin_box.setValue(0)
            self._size_label.setText('')
            self._color_label.setText('')
            self._end_label.setText('')
            self._current_color = None
            enabled = False
        else:
            self._name_text.setText(f"{section.name}")
            self._start_spin_box.setMinimum(0)
            self._start_spin_box.setMaximum(section.parent.size - 1 if section.parent else 0xFFFF)
            self._start_spin_box.setValue(section.relative_start)
            self._current_color = section.color

            editor_type = _editor_for_type(type(section))
            if editor_type != type(self._section_editor):
                layout = self._section_editor_container.layout()
                assert layout is not None
                # Remove children of section editor
                if self._section_editor is not None:
                    self._section_editor.setParent(None)
                    self._section_editor.deleteLater()
                    self._section_editor = None
                # Add new section editor
                assert issubclass(editor_type, SectionDetailsWidgetBase)
                self._section_editor = editor_type(self)
                layout.addWidget(self._section_editor)
                self._section_editor.data_changed.connect(self._on_editor_change)
            assert self._section_editor is not None
            self._section_editor.section = section
            self._update_size_and_end()
            enabled = True
        self._update_color_label()

        self._name_text.setEnabled(enabled)
        self._start_spin_box.setEnabled(enabled)
        self._size_label.setEnabled(enabled)
        self._color_label.setEnabled(enabled)

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
        self._size_is_hex = is_hex
        self._update_size_and_end()

    def _toogle_end_label(self, is_hex: bool) -> None:
        '''Toggle the end text between hex and decimal.'''
        self._end_is_hex = is_hex
        self._update_size_and_end()

    def _update_color_label(self):
        '''Updates the color label.'''
        color_name = self._current_color.name() if self._current_color else 'None'
        if self._current_color and self._current_color.alpha() < 255:
            color_name += f"{self._current_color.alpha():02X}"
        self._color_label.setText(color_name)
        self._color_label.setStyleSheet(f"background-color: {self._current_color.name() if self._current_color else 'transparent'}")
        self._color_button.setEnabled(True)

    def _on_editor_change(self) -> None:
        '''Handle changes from the section editor widget.'''
        self._update_size_and_end()
        errors = self._section_editor.get_errors() if self._section_editor else []
        self._error_label.setText("\n".join(errors))
        changes = self._section_editor.has_changes() if self._section_editor else False
        self._save_button.setEnabled(len(errors) == 0 and changes)
        self._discard_button.setEnabled(changes)

    def _update_size_and_end(self) -> None:
        '''Update the size and end labels based on the current start and size.'''
        if self._section is None or self._section_editor is None:
            return
        size = self._section_editor.get_size()
        end = self._section.relative_start + size
        if self._size_is_hex:
            self._size_label.setText(f"0x{size:X}")
        else:
            self._size_label.setText(f"{size}")
        if self._end_is_hex:
            self._end_label.setText(f"0x{end:X}")
        else:
            self._end_label.setText(f"{end}")

    def _on_change(self) -> None:
        '''Handle changes to the section information.'''
        change = False
        error = ''
        if self._section is None:
            change = False
        else:
            name = self._name_text.text()
            relative_start = int(self._start_spin_box.text(), 16)
            parent_absolute_start = self._section.parent.absolute_start if self._section.parent else 0
            absolute_start = parent_absolute_start + relative_start
            size = self._section.size
            self._end_label.setText(f"0x{relative_start + size:X}")
            s = self._section
            if s.name != name or s.absolute_start != absolute_start or s.size != size or s.color != self._current_color:
                parent_absolute_end = self._section.parent.absolute_end if self._section.parent else 0xFFFF
                if absolute_start < parent_absolute_start or absolute_start + size > parent_absolute_end:
                    error = "Section is out of bounds of parent section."
                else:
                    overlaps = self._section.parent.get_overlaps(absolute_start, size) if self._section.parent else []
                    if overlaps and (len(overlaps) == 1 and overlaps[0] != self._section):
                        error = "Section overlaps with existing sibling sections."
                change = True
            else:
                change = False
        self._save_button.setEnabled(change)
        self._discard_button.setEnabled(change)
        self._error_label.setText(error)
        self._error_label.setEnabled(len(error) > 0)

    def _on_save(self) -> None:
        '''Save the changes to the section.'''
        if self._section is None or self._section_editor is None:
            return
        self._section_editor.save_section()
        self._section.name = self._name_text.text()
        self._section.relative_start = int(self._start_spin_box.text(), 16)
        self._section.color = self._current_color
        self.section_changed.emit()
        self._on_change()

    def _on_discard(self) -> None:
        '''Discard the changes to the section.'''
        if self._section is None:
            return
        self.set_section(self._section)

    def _on_color_button_clicked(self) -> None:
        '''Handle the color button click event.'''
        if self._section is None:
            return
        c = self._section.color if self._section.color else QColor(255, 255, 255)
        f = QColorDialog.ColorDialogOption.ShowAlphaChannel | \
            QColorDialog.ColorDialogOption.DontUseNativeDialog
        color = QColorDialog.getColor(c, self, "Segment Color", f)
        if color.isValid():
            if color.alpha() == 0:
                color = None
            self._current_color = color
            self._update_color_label()
            self._on_change()

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
        self.setText('H' if self._is_hex else 'D')
        self.setToolTip('Hexadecimal' if self._is_hex else 'Decimal')
        self.toggle_signal.emit(self._is_hex)

T = TypeVar('T', bound=Section, covariant=True)
class SectionDetailsWidgetBase(QWidget, Generic[T]):
    '''Base class for section details widgets.'''
    data_changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._section: T | None = None

    @property
    def section(self) -> T | None:
        '''Get the currently displayed section.'''
        return self._section
    @section.setter
    def section(self, section: T | None) -> None:
        '''Set the displayed section information.'''
        self._section = section
        self._on_section_change()

    @abstractmethod
    def save_section(self) -> None:
        '''Save the changes to the section.'''
        assert False, "Subclasses must implement this method."

    @abstractmethod
    def has_changes(self) -> bool:
        '''Check if there are unsaved changes to the section.'''
        assert False, "Subclasses must implement this method."

    @abstractmethod
    def get_size(self) -> int:
        '''Get the size of the section being edited.'''
        assert False, "Subclasses must implement this method."

    @abstractmethod
    def get_errors(self) -> list[str]:
        '''Get a list of errors that prevent the section from being saved.'''
        assert False, "Subclasses must implement this method."

    @abstractmethod
    def _on_section_change(self) -> None:
        '''Handle changes to the section information.'''
        assert False, "Subclasses must implement this method."
