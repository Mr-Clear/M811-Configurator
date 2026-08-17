from typing import TYPE_CHECKING

from mouse_data.observable_value import Value

if TYPE_CHECKING:
    from . import MouseData

class Color(Value):
    """Represents a color setting."""
    def __init__(self, mouse: MouseData, offset: int):
        super().__init__(mouse, offset, 3)

    @property
    def rgb(self) -> tuple[int, int, int]:
        return tuple(self.raw_data) # type: ignore
    @rgb.setter
    def rgb(self, value: tuple[int, int, int]) -> None:
        if len(value) != 3 or any(not (0 <= v <= 255) for v in value):
            raise ValueError(f"Color must be a tuple of 3 integers between 0 and 255, got {value}")
        self._mouse.set_value(self.offset, bytes(value))

    def to_json(self) -> list[object]:
        return list(self.rgb)
