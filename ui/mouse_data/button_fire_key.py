from enum import Enum

from ui.keyboard import ScanCode
from ui.mouse_data import MouseData
from ui.mouse_data.button import Button


class ButtonFireKey(Button):
    ''' Presses a mouse button or keyboard key several times '''
    class FireMouseButton(Enum):
        LEFT = 0x81
        RIGHT = 0x82
        MIDDLE = 0x84

    def __init__(self, mouse: MouseData, offset: int):
        super().__init__(mouse, offset)

    @classmethod
    def type_name(cls) -> str:
        return "Fire Key"

    @classmethod
    def is_data_valid(cls, mouse: MouseData, offset: int) -> bool:
        data = list(mouse.data[offset:offset + Button.DATA_LENGTH])
        if data[0] != 0x99:
            return False
        if data[1] not in [button.value for button in ButtonFireKey.FireMouseButton] and \
           data[1] not in [scan_code.code for scan_code in ScanCode]:
            return False
        return True

    def set_default(self) -> None:
        self.raw_data = bytes([
            0x99,
            ScanCode.A.code,
            5,  # repeat count
            10, # delay in 10ms
        ])

    @property
    def key(self) -> ScanCode | FireMouseButton:
        if self.raw_data[1] in [button.value for button in ButtonFireKey.FireMouseButton]:
            return ButtonFireKey.FireMouseButton(self.raw_data[1])
        return ScanCode.from_code(self.raw_data[1])
    @key.setter
    def key(self, value: ScanCode | FireMouseButton) -> None:
        data = bytearray(self.raw_data)
        if isinstance(value, ScanCode):
            data[1] = value.code
        else:
            data[1] = value.value
        self.raw_data = data

    @property
    def repeat_count(self) -> int:
        return self.raw_data[2]
    @repeat_count.setter
    def repeat_count(self, value: int) -> None:
        if not (1 <= value <= 255):
            raise ValueError(f"Repeat count must be between 1 and 255, got {value}")
        data = bytearray(self.raw_data)
        data[2] = value
        self.raw_data = data

    @property
    def delay(self) -> int:
        return self.raw_data[3] * 10
    @delay.setter
    def delay(self, value: int) -> None:
        if not (value <= 2550):
            raise ValueError(f"Maximum delay is 2550 ms, got {value}")
        data = bytearray(self.raw_data)
        data[3] = value // 10
        self.raw_data = data

    def __str__(self) -> str:
        return f'({self.key.name}, times {self.repeat_count}, delay {self.delay}ms)'
