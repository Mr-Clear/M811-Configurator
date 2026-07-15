from enum import Enum

from ui.mouse_data import MouseData
from ui.mouse_data.button import Button


class ButtonMouseButton(Button):
    ''' Button that is mapped to a mouse button. '''
    class Type(Enum):
        LEFT = 0x81
        RIGHT = 0x82
        MIDDLE = 0x83
        BACK = 0x84
        FORWARD = 0x85
        SCROLL_UP = 0x8B
        SCROLL_DOWN = 0x8C

        @property
        def name(self) -> str:
            return self._name_.replace("_", " ").title()

    def __init__(self, mouse: MouseData, offset: int):
        data = list(mouse.data[offset:offset + 4])
        if data[1] != 0x00 or data[2] != 0x00 or data[3] != 0x00:
            raise ValueError(f"Invalid MouseButton data: {data}")
        if data[0] not in [button.value for button in ButtonMouseButton.Type]:
            raise ValueError(f"Invalid mouse button type: {data[0]}")
        self.mouse_button_type = ButtonMouseButton.Type(data[0])
        super().__init__(mouse, offset)

    @classmethod
    def type_name(cls) -> str:
        return "Mouse Button"

    def to_raw(self) -> list[int]:
        return [self.mouse_button_type.value, 0x00, 0x00, 0x00]

    def __str__(self) -> str:
        return f"{self.mouse_button_type.name.title()}"
