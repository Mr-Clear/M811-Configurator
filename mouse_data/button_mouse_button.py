from enum import Enum

from mouse_data import MouseData
from mouse_data.button import Button


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
        super().__init__(mouse, offset)

    @classmethod
    def type_name(cls) -> str:
        return "Mouse Button"

    @classmethod
    def is_data_valid(cls, mouse: MouseData, offset: int) -> bool:
        data = list(mouse.data[offset:offset + Button.DATA_LENGTH])
        if data[0] not in [button.value for button in ButtonMouseButton.Type]:
            return False
        if data[1] != 0x00 or data[2] != 0x00 or data[3] != 0x00:
            return False
        return True

    def set_default(self) -> None:
        self.raw_data = bytes([
            ButtonMouseButton.Type.LEFT.value,
            0x00,
            0x00,
            0x00
        ])

    @property
    def mouse_button_type(self) -> Type:
        ''' The type of the mouse button. '''
        return ButtonMouseButton.Type(self.raw_data[0])
    @mouse_button_type.setter
    def mouse_button_type(self, mouse_button_type: Type) -> None:
        ''' Set the type of the mouse button. '''
        data = bytearray(self.raw_data)
        data[0] = mouse_button_type.value
        self.raw_data = data

    def __str__(self) -> str:
        return f"{self.mouse_button_type.name.title()}"
