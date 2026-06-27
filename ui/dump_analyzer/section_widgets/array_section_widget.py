"""Widget to edit array section details."""

from PySide6.QtWidgets import QComboBox, QFormLayout, QSpinBox, QToolButton, QWidget

from ..sections.array_section import ArraySection
from ..sections.section import Section
from .section_types import get_section_types
from .section_widget import SectionDetailsWidgetBase
from .clipboard import get_section_from_clipboard


class ArraySectionWidget(SectionDetailsWidgetBase[ArraySection]):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._section_types = list(get_section_types().keys())
        self._unsaved_section: Section | None = None
        layout = QFormLayout(self)
        self.setLayout(layout)
        self._child_type_combo_box = QComboBox(self)
        for section_type in self._section_types:
            self._child_type_combo_box.addItem(section_type.type_name())
        self._child_type_combo_box.currentIndexChanged.connect(self.data_changed)
        layout.addRow("Child Type:", self._child_type_combo_box)

        self.paste_button = QToolButton(self)
        self.paste_button.setText("📋 Paste Child from Clipboard")
        self.paste_button.clicked.connect(self._on_paste_clicked)
        self.paste_button.setEnabled(get_section_from_clipboard() is not None)
        layout.addRow(self.paste_button)

        self.repetitions_spin_box = QSpinBox(self)
        self.repetitions_spin_box.setMinimum(1)
        self.repetitions_spin_box.setMaximum(1000)
        self.repetitions_spin_box.valueChanged.connect(self.data_changed)
        self.repetitions_spin_box.valueChanged.connect(self._clear_unsaved_section)
        layout.addRow("Count:", self.repetitions_spin_box)

        self.gap_spin_box = QSpinBox(self)
        self.gap_spin_box.setMinimum(0)
        self.gap_spin_box.setMaximum(1000)
        self.gap_spin_box.valueChanged.connect(self.data_changed)
        layout.addRow("Gap:", self.gap_spin_box)

        self.padding_spin_box = QSpinBox(self)
        self.padding_spin_box.setMinimum(0)
        self.padding_spin_box.setMaximum(1000)
        self.padding_spin_box.valueChanged.connect(self.data_changed)
        layout.addRow("Padding:", self.padding_spin_box)


    def save_section(self) -> None:
        '''Save the changes to the section.'''
        if not self.section:
            return
        if self._unsaved_section:
            self.section.child_section = self._unsaved_section
        elif self.section.child_section is None or type(self.section.child_section) != self._selected_type():
            old_child = self.section.child_section
            self.section.child_section = self._selected_type()(f'New {self._selected_type().type_name()}', 0, self.section)
            if old_child:
                self.section.child_section.relative_start = old_child.relative_start
                self.section.child_section.color = old_child.color
        self.section.repetitions = self.repetitions_spin_box.value()
        self.section.gap = self.gap_spin_box.value()
        self.section.padding = self.padding_spin_box.value()

    def has_changes(self) -> bool:
        '''Check if there are unsaved changes to the section.'''
        if not self.section:
            return False
        if not self.section.child_section:
            return True
        return self._unsaved_section is not None or \
               type(self.section.child_section) != self._selected_type() or \
               self.section.repetitions != self.repetitions_spin_box.value() or \
               self.section.gap != self.gap_spin_box.value() or \
               self.section.padding != self.padding_spin_box.value()

    def get_size(self) -> int:
        '''Get the size of the section being edited.'''
        if not self.section or not self.section.child_section:
            return 0
        c = self.section.child_section
        return c.relative_start + \
               (c.size + self.gap_spin_box.value()) * self.repetitions_spin_box.value() - self.gap_spin_box.value() + \
               self.padding_spin_box.value()

    def get_errors(self) -> list[str]:
        '''Get a list of errors that prevent the section from being saved.'''
        return []

    def _on_section_change(self) -> None:
        '''Handle changes to the section information.'''
        if not self.section or not self.section.child_section:
            return
        self._child_type_combo_box.setCurrentIndex(self._section_types.index(type(self.section.child_section)))
        self.repetitions_spin_box.setValue(self.section.repetitions)
        self.gap_spin_box.setValue(self.section.gap)
        self.padding_spin_box.setValue(self.section.padding)

    def _selected_type(self) -> type[Section]:
        return self._section_types[self._child_type_combo_box.currentIndex()]

    def _clear_unsaved_section(self, _: int) -> None:
        self._unsaved_section = None

    def _on_paste_clicked(self) -> None:
        '''Handle the paste button being clicked.'''
        if self.section is None:
            return
        section = get_section_from_clipboard()
        if section is None:
            return
        self._child_type_combo_box.setCurrentIndex(self._section_types.index(type(section)))
        section.relative_start = 0
        section.parent = self.section
        self._unsaved_section = section
        self.data_changed.emit()
