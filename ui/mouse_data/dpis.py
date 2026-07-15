from typing import TYPE_CHECKING

from ui.mouse_data.observable_value import Observable, Value

if TYPE_CHECKING:
    from . import MouseData

class Dpi(Value):
    """Represents a single DPI setting of the mouse."""
    def __init__(self, mouse: MouseData, offset: int):
        super().__init__(mouse, offset, 2)

    @property
    def value(self) -> int:
        return int.from_bytes(self.raw_data, byteorder='little')
    @value.setter
    def value(self, value: int) -> None:
        min_dpi = min(DPI_VALUES.keys())
        max_dpi = max(DPI_VALUES.keys())
        if not (min_dpi <= value <= max_dpi):
            raise ValueError(f"Value must be between {min_dpi} and {max_dpi}, got {value}")
        if value not in DPI_VALUES:
            raise ValueError(f"Value must be one of {list(DPI_VALUES.keys())}, got {value}")
        self._mouse.set_value(self.offset, value.to_bytes(2, byteorder='little'))

    def to_json(self) -> int:
        return self.value


class Dpis(Observable):
    """All DPI settings for one mode"""
    def __init__(self, mouse: MouseData, dpis: list[Dpi]):
        super().__init__(mouse)
        self._dpis = dpis

    def value(self, index: int) -> int:
        return self._dpis[index].value
    def set_value(self, index: int, value: int) -> None:
        self._dpis[index].value = value

    def to_json(self) -> list[object]:
        return [dpis.value for dpis in self._dpis]


def _build_dpi_values() -> dict[int, tuple[int, int]]:
    values: dict[int, tuple[int, int]] = {}

    # 200..6200 in 100-DPI steps: low byte increases by +2, with +3 at specific steps.
    low_byte = 0x04
    values[200] = (low_byte, 0)
    plus_three_steps = {2, 6, 10, 14, 17, 21, 25, 29, 32, 36, 40, 43, 47, 51, 54, 59}
    for step, dpi in enumerate(range(300, 6300, 100), start=1):
        low_byte += 3 if step in plus_three_steps else 2
        values[dpi] = (low_byte, 0)

    # 6400..12400 in 200-DPI steps: reuse low bytes from 3200..6200 with high byte set.
    for dpi in range(6400, 12401, 200):
        base_dpi = dpi // 2
        values[dpi] = (values[base_dpi][0], 1)

    return values
DPI_VALUES: dict[int, tuple[int, int]] = _build_dpi_values()

def dpi_to_int(dpi: tuple[int, int]) -> int:
    ''' Converts a tuple of 2 integers representing the low and high bytes of a DPI level to an integer. '''
    if len(dpi) != 2:
        raise ValueError('DPI data must be a tuple of 2 integers.')
    for value, data in DPI_VALUES.items():
        if data == dpi:
            return value
    raise ValueError(f"Unknown DPI value for data: {dpi}")

def int_to_dpi(value: int) -> tuple[int, int]:
    ''' Converts an integer DPI value to a tuple of 2 integers representing the low and high bytes of the DPI level. '''
    if value not in DPI_VALUES:
        raise ValueError(f"Unknown DPI value: {value}")
    return DPI_VALUES[value]
