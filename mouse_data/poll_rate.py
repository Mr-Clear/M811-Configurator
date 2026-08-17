from typing import TYPE_CHECKING

from mouse_data.observable_value import IntValue

if TYPE_CHECKING:
    from . import MouseData

class PollRate(IntValue):
    """Represents a single poll rate of the mouse."""
    def __init__(self, mouse: MouseData, offset: int):
        super().__init__(mouse, offset, 1, 0, 255)
