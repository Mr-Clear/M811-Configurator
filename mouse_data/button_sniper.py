from mouse_data import MouseData
from mouse_data.button import Button
from mouse_data.dpis import dpi_to_int


class ButtonSniper(Button):
    ''' Button that sets the DPI to a predefined sniper level while held. '''

    def __init__(self, mouse: MouseData, offset: int):
        super().__init__(mouse, offset)

    @classmethod
    def type_name(cls) -> str:
        return "Sniper"

    @classmethod
    def is_data_valid(cls, mouse: MouseData, offset: int) -> bool:
        data = list(mouse.data[offset:offset + Button.DATA_LENGTH])
        try:
            dpi_to_int((data[2], data[1] - 1))
        except ValueError:
            return False
        if data[0] != 0x9a:
            return False
        return True

    def set_default(self) -> None:
        self.raw_data = bytes([
            0x9a,
            0x01,  # DPI level (1-16)
            0x18,  # DPI value (low byte)
            0x00,  # reserved
        ])

    @property
    def dpi(self) -> int:
        ''' The DPI level of the sniper button. '''
        return dpi_to_int((self.raw_data[2], self.raw_data[1] - 1))
    @dpi.setter
    def dpi(self, value: int) -> None:
        ''' Set the DPI level of the sniper button. '''
        if value < 100 or value > 16000:
            raise ValueError(f"DPI must be between 100 and 16000, got {value}")
        data = bytearray(self.raw_data)
        dpi_tuple = (value // 100, (value % 100) + 1)
        data[1] = dpi_tuple[1]
        data[2] = dpi_tuple[0]
        self.raw_data = data

    def __str__(self) -> str:
        return f'{self.dpi} DPI'
