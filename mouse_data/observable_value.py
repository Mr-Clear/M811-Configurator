from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, Signal

from mouse_data.usb_connection import UsbConnection

if TYPE_CHECKING:
    from . import MouseData

class Observable(QObject):
    changed = Signal()

    def __init__(self, mouse: MouseData):
        super().__init__()
        self._mouse = mouse

    @abstractmethod
    def to_json(self) -> dict[str, object] | list[object] | str | int | float | bool | None:
        pass


class Value(Observable):
    def __init__(self, mouse: MouseData, offset: int, length: int) -> None:
        super().__init__(mouse)
        self._offset = offset
        self._length = length
        self._mouse.register_value(self)
        if self.__class__ is Value:
            raise TypeError("Value is an abstract class and cannot be instantiated directly.")

    @property
    def mouse_data(self) -> MouseData:
        return self._mouse

    @property
    def offset(self) -> int:
        return self._offset

    @property
    def length(self) -> int:
        return self._length

    @property
    def end_offset(self) -> int:
        return self.offset + self.length - 1

    @property
    def raw_data(self) -> memoryview:
        return self.mouse_data.data[self.offset:self.offset + self.length].toreadonly()
    @raw_data.setter
    def raw_data(self, value: bytes | bytearray | memoryview) -> None:
        if len(value) != self.length:
            raise ValueError(f"Data length must be {self.length}, got {len(value)}")
        self.mouse_data.set_value(self.offset, value)

    def contains_offset(self, offset: int) -> bool:
        return self.offset <= offset < self.offset + self.length

    def load_from_mouse(self, connection: UsbConnection) -> None:
        """Load the value from the mouse device."""
        data = connection.read(self.offset, self.length)
        self.raw_data = data

    def __len__(self) -> int:
        return self.length

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(0x{self.offset:04X}-0x{self.end_offset:04X})'

class IntValue(Value):
    """Represents an integer."""
    def __init__(self, mouse: MouseData, offset: int, length: int, min: int, max: int):
        super().__init__(mouse, offset, length)
        self._min = min
        self._max = max

    @property
    def value(self) -> int:
        return self.raw_data[0]
    @value.setter
    def value(self, value: int) -> None:
        if not (self._min <= value <= self._max):
            raise ValueError(f"Value must be between {self._min} and {self._max}, got {value}")
        self._mouse.set_value(self.offset, bytes([value]))

    def to_json(self) -> int:
        return self.value
