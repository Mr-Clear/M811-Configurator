"""Widget to display and edit a value section."""

from PySide6.QtWidgets import QComboBox, QFormLayout, QLabel, QWidget

from ui.dump_analyzer.section_value import SectionValue

from .section_widget import SectionDetailsWidgetBase
from .spin_box import SpinBox


class SectionValueWidget(SectionDetailsWidgetBase[SectionValue]):
    '''Widget to display and edit a value section.'''
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        max_bits = 2 ** 8 - 1

        layout = QFormLayout(self)
        self._size_combo = QComboBox(self)
        self._size_combo.addItems(["1 byte", "2 bytes", "4 bytes", "8 bytes"])
        self._size_combo.currentIndexChanged.connect(self._on_data_changed)
        layout.addRow(QLabel("Size:", self), self._size_combo)
        self._min_value_spin = SpinBox(self)
        self._min_value_spin.setRange(0, max_bits)
        layout.addRow(QLabel("Min Value:", self), self._min_value_spin)
        self._max_value_spin = SpinBox(self)
        self._max_value_spin.setRange(0, max_bits)
        self._max_value_spin.setValue(max_bits)
        layout.addRow(QLabel("Max Value:", self), self._max_value_spin)
        self._min_value_spin.valueChanged.connect(self._on_data_changed)
        self._max_value_spin.valueChanged.connect(self._on_data_changed)

    @staticmethod
    def _index_to_size(index: int) -> int:
        '''Get the current size of the section being edited.'''
        return 2 ** index

    @staticmethod
    def _size_to_index(size: int) -> int:
        '''Get the index of the size combo box for the given size.'''
        return {1: 0, 2: 1, 4: 2, 8: 3}.get(size, 0)

    def _on_data_changed(self) -> None:
        '''Update UI when data changes.'''

        last_max = self._max_value_spin.value() == self._max_value_spin.maximum()
        max_bits = 2 ** (self.get_size() * 8) - 1
        self._min_value_spin.setMaximum(max_bits)
        self._max_value_spin.setMaximum(max_bits)
        if last_max:
            self._max_value_spin.setValue(max_bits)
        self.data_changed.emit()

    def save_section(self) -> None:
        '''Save the changes to the section.'''
        if self.section is None:
            return
        self.section.byte_count = self._index_to_size(self._size_combo.currentIndex())

    def has_changes(self) -> bool:
        '''Check if there are unsaved changes to the section.'''
        if self.section is None:
            return False

        return self._size_combo.currentIndex() != self._size_to_index(self.section.byte_count) or \
               self._min_value_spin.value() != self.section.min_value or \
               self._max_value_spin.value() != self.section.max_value

    def get_size(self) -> int:
        '''Get the size of the section being edited.'''
        index = self._size_combo.currentIndex()
        size = self._index_to_size(index)
        return size

    def get_errors(self) -> list[str]:
        '''Get a list of errors that prevent the section from being saved.'''
        if self.section is not None:
            min_value = self._min_value_spin.value()
            max_value = self._max_value_spin.value()
            if min_value > max_value:
                return ["Min value cannot be greater than max value."]
        return []

    def _on_section_change(self) -> None:
        '''Handle changes to the section information.'''
        section = self.section
        if section is None:
            self._size_combo.setCurrentIndex(0)
            self._size_combo.setEnabled(False)
            return
        self._size_combo.setCurrentIndex(self._size_to_index(section.byte_count))
        self._size_combo.setEnabled(True)
