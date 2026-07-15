from ui.mouse_data import MouseData
from ui.mouse_data.button import Button
from ui.mouse_data.dpis import dpi_to_int


class ButtonSniper(Button):
    ''' Button that sets the DPI to a predefined sniper level while held. '''

    def __init__(self, mouse: MouseData, offset: int):
        data = list(mouse.data[offset:offset + 4])
        if data[0] != 0x9a:
            raise ValueError(f"Invalid Sniper data: {data}")
        self.dpi_level = (data[2], data[1] - 1)
        super().__init__(mouse, offset)

    @classmethod
    def type_name(cls) -> str:
        return "Sniper"

    @property
    def dpi(self) -> int:
        ''' The DPI level of the sniper button. '''
        return dpi_to_int(self.dpi_level)

    def to_raw(self) -> list[int]:
        return [0x9a, self.dpi_level[1] + 1, self.dpi_level[0], self.dpi_level[0]]

    def __str__(self) -> str:
        return f'{self.dpi} DPI'
