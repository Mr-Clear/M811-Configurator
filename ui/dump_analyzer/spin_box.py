"""A QSpinBox that can handle values larger than 2^31-1."""

from PySide6.QtCore import Signal
from PySide6.QtGui import QValidator
from PySide6.QtWidgets import QAbstractSpinBox, QWidget


class _UIntValidator(QValidator):
    '''A QIntValidator that can handle values larger than 2^31-1.'''
    def __init__(self, min: int = 0, max: int = 2**64 - 1, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._min = min
        self._max = max

    def validate(self, input: str, pos: int) -> QValidator.State:
        '''Validate the input.'''
        if not input:
            return QValidator.State.Intermediate
        try:
            value = int(input)
            if self._min <= value <= self._max:
                return QValidator.State.Acceptable
            else:
                return QValidator.State.Invalid
        except ValueError:
            return QValidator.State.Invalid

    @property
    def min(self) -> int:
        return self._min
    @min.setter
    def min(self, value: int) -> None:
        self._min = value

    @property
    def max(self) -> int:
        return self._max
    @max.setter
    def max(self, value: int) -> None:
        self._max = value

class SpinBox(QAbstractSpinBox):
    '''A QSpinBox that can handle values larger than 2^31-1.'''
    valueChanged = Signal("quint64") # type: ignore

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._value = 0
        self._min_value = 0
        self._max_value = 2**64 - 1
        self._validator = _UIntValidator(self._min_value, self._max_value, self)
        self.lineEdit().setText(str(self._value))
        self.lineEdit().setValidator(self._validator)
        self.lineEdit().textChanged.connect(self._on_editing)

    def _on_editing(self) -> None:
        '''Handle the editing finished signal from the line edit.'''
        curser_pos = self.lineEdit().cursorPosition()
        try:
            value = int(self.lineEdit().text())
            self.setValue(value)
        except ValueError:
            self.lineEdit().setText(str(self._value))
        self.lineEdit().setCursorPosition(curser_pos)

    def setValue(self, value: int) -> None:
        '''Set the value of the spin box.'''
        if value == self._value:
            return
        self._value = max(self._min_value, min(self._max_value, value))
        self.lineEdit().setText(str(self._value))
        self.valueChanged.emit(self._value)
    def value(self) -> int:
        '''Get the current value of the spin box.'''
        return self._value

    def setMinimum(self, min_value: int) -> None:
        '''Set the minimum value of the spin box.'''
        if min_value > self._max_value:
            min_value = self._max_value
        if min_value == self._min_value:
            return
        self._min_value = min_value
        if self._value < self._min_value:
            self.setValue(self._min_value)
        self._validator.max = self._max_value
    def minimum(self) -> int:
        '''Get the minimum value of the spin box.'''
        return self._min_value

    def setMaximum(self, max_value: int) -> None:
        '''Set the maximum value of the spin box.'''
        if max_value < self._min_value:
            max_value = self._min_value
        if max_value == self._max_value:
            return
        self._max_value = max_value
        if self._value > self._max_value:
            self.setValue(self._max_value)
    def maximum(self) -> int:
        '''Get the maximum value of the spin box.'''
        return self._max_value

    def setRange(self, min_value: int, max_value: int) -> None:
        '''Set the minimum and maximum values of the spin box.'''
        self.setMinimum(min_value)
        self.setMaximum(max_value)

    def stepBy(self, steps: int) -> None:
        '''Step the value by the given number of steps.'''
        step_size = 1  # You can adjust this to change the step size
        self.setValue(self._value + steps * step_size)

    def stepEnabled(self) -> QAbstractSpinBox.StepEnabledFlag:
        '''Return which step buttons should be enabled.'''
        flags = QAbstractSpinBox.StepEnabledFlag(0)
        if self._value > self._min_value:
            flags |= QAbstractSpinBox.StepEnabledFlag.StepDownEnabled
        if self._value < self._max_value:
            flags |= QAbstractSpinBox.StepEnabledFlag.StepUpEnabled
        return flags
