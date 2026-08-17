from typing import TYPE_CHECKING

from .observable_value import IntValue

if TYPE_CHECKING:
    from . import MouseData


class ActiveMode(IntValue):
    """Represents the active mode of the mouse."""
    def __init__(self, mouse: MouseData, offset: int):
        super().__init__(mouse, offset, 1, 0, 4)
