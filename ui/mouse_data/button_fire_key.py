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
        data = list(mouse.data[offset:offset + 4])
        if data[0] != 0x99:
            raise ValueError(f"Invalid FireKey data: {data}")
        self.key: ScanCode | ButtonFireKey.FireMouseButton
        if data[1] in [button.value for button in ButtonFireKey.FireMouseButton]:
            self.key = ButtonFireKey.FireMouseButton(data[1])
        elif data[1] in [scan_code.code for scan_code in ScanCode]:
            self.key = ScanCode.from_code(data[1])
        else:
            raise ValueError(f"Invalid key for FireKey: {data[1]:#02x}")
        self.repeat_count = data[2]
        self.delay = data[3] * 10
        super().__init__(mouse, offset)

    @classmethod
    def type_name(cls) -> str:
        return "Fire Key"

    def to_raw(self) -> list[int]:
        return [0x99, self.key.value
                if isinstance(self.key, ButtonFireKey.FireMouseButton)
                else self.key.code, self.repeat_count, self.delay // 10]

    def __str__(self) -> str:
        return f'({self.key.name}, times {self.repeat_count}, delay {self.delay}ms)'
