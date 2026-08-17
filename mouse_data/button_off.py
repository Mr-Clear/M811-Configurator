from mouse_data import MouseData
from mouse_data.button import Button


class ButtonOff(Button):
    ''' Button without functionality. '''

    def __init__(self, mouse: MouseData, offset: int):
        super().__init__(mouse, offset)

    @classmethod
    def type_name(cls) -> str:
        return "Off"

    @classmethod
    def is_data_valid(cls, mouse: MouseData, offset: int) -> bool:
        data = list(mouse.data[offset:offset + Button.DATA_LENGTH])
        return data == [0x00, 0x00, 0x00, 0x00]

    def set_default(self) -> None:
        self.raw_data = bytes([0x00, 0x00, 0x00, 0x00])

    def __str__(self) -> str:
        return "Button Off"
