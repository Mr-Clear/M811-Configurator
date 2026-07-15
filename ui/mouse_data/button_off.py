from ui.mouse_data import MouseData
from ui.mouse_data.button import Button


class ButtonOff(Button):
    ''' Button without functionality. '''

    def __init__(self, mouse: MouseData, offset: int):
        data = list(mouse.data[offset:offset + 4])
        if data != [0x00, 0x00, 0x00, 0x00]:
            raise ValueError(f"Invalid ButtonOff data: {data}")
        super().__init__(mouse, offset)

    @classmethod
    def type_name(cls) -> str:
        return "Off"

    def to_raw(self) -> list[int]:
        return [0x00, 0x00, 0x00, 0x00]

    def __str__(self) -> str:
        return "Button Off"
