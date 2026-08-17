from mouse_data import MouseData
from mouse_data.button import Button


class ButtonCustom(Button):
    ''' Button with a custom function defined by the user. '''
    def __init__(self, mouse: MouseData, offset: int):
        super().__init__(mouse, offset)

    @classmethod
    def type_name(cls) -> str:
        return "❗Custom❗"

    @classmethod
    def is_data_valid(cls, mouse: MouseData, offset: int) -> bool:
        return True  # Accept any data as valid for custom buttons

    @property
    def data(self) -> list[int]:
        ''' The raw data of the button. '''
        return list(self.raw_data)

    def set_default(self) -> None:
        pass  # No default data for custom buttons

    def __str__(self) -> str:
        return f'{self.data}'
