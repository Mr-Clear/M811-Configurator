from enum import Enum

class ValueFunction(Enum):
    """An enumeration of the different functions that can be assigned to a section."""
    NONE = 0
    ACTIVE_MODE = 1
    BUTTON = 2
    BUTTON_LIST = 3
    DPI = 4
    DPI_LIST = 5
    EFFECT = 6
    MACRO_STEP = 7
    MACRO = 8
    MODE_COLOR = 9
    POLL_RATE = 10
    SCROLL_SPEED = 11

    def __str__(self) -> str:
        return self.name.replace("_", " ").title()
