from typing import TYPE_CHECKING

from mouse_data.observable_value import Value

if TYPE_CHECKING:
    from . import MouseData

class ScrollSpeed(Value):
    """Represents the scroll speed of the mouse."""
    def __init__(self, mouse: MouseData, offset: int):
        super().__init__(mouse, offset, 1)

    @property
    def value(self) -> int:
        return self.raw_data[0]
    @value.setter
    def value(self, value: int) -> None:
        if not (0 <= value <= 255):
            raise ValueError(f"Scroll speed must be between 0 and 255, got {value}")
        self._mouse.set_value(self.offset, bytes([value]))

    def to_json(self) -> int:
        return self.value
