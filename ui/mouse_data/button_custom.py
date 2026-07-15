from ui.mouse_data import MouseData
from ui.mouse_data.button import Button


class ButtonCustom(Button):
    ''' Button with a custom function defined by the user. '''
    def __init__(self, mouse: MouseData, offset: int):
        data = list(mouse.data[offset:offset + 4])
        if data[0] != 0x00:
            raise ValueError(f"Invalid Custom button data: {data}")
        self.data = data
        super().__init__(mouse, offset)

    @classmethod
    def type_name(cls) -> str:
        return "❗Custom❗"

    def to_raw(self) -> list[int]:
        return self.data

    def __str__(self) -> str:
        return f'{self.data}'
