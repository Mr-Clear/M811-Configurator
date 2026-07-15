from enum import Enum

from ui.mouse_data import MouseData
from ui.mouse_data.button import Button


class ButtonMouseFunction(Button):
    ''' Button that is mapped to a mouse function. '''
    class Type(Enum):
        DPI_PLUS = [0x8a, 0x00, 0x00, 0x00]
        DPI_MINUS = [0x89, 0x00, 0x00, 0x00]
        SWITCH_MODE = [0x8d, 0x00, 0x00, 0x00]
        MODE_PLUS = [0x94, 0x00, 0x00, 0x00]
        MODE_MINUS = [0x95, 0x00, 0x00, 0x00]
        DPI_SWITCH = [0x88, 0x00, 0x00, 0x00]
        DPI_UP = [0x89, 0x00, 0x00, 0x00]
        DPI_DOWN = [0x8a, 0x00, 0x00, 0x00]
        LED_SWITCH = [0x9b, 0x04, 0x00, 0x00]
        POLL_RATE_PLUS = [0x97, 0x00, 0x00, 0x00]
        POLL_RATE_MINUS = [0x98, 0x00, 0x00, 0x00]
        RESET_SETTINGS = [0x9b, 0x02, 0x00, 0x00]
        DPI_LED_MODE = [0x9b, 0x02, 0x00, 0x00]

        @staticmethod
        def names() -> dict[ButtonMouseFunction.Type, str]:
            return {
                ButtonMouseFunction.Type.DPI_PLUS: "DPI+",
                ButtonMouseFunction.Type.DPI_MINUS: "DPI-",
                ButtonMouseFunction.Type.SWITCH_MODE: "Switch Mode",
                ButtonMouseFunction.Type.MODE_PLUS: "Mode+",
                ButtonMouseFunction.Type.MODE_MINUS: "Mode-",
                ButtonMouseFunction.Type.DPI_SWITCH: "DPI Switch",
                ButtonMouseFunction.Type.LED_SWITCH: "LED Switch",
                ButtonMouseFunction.Type.POLL_RATE_PLUS: "Poll Rate+",
                ButtonMouseFunction.Type.POLL_RATE_MINUS: "Poll Rate-",
                ButtonMouseFunction.Type.RESET_SETTINGS: "Reset Settings",
                ButtonMouseFunction.Type.DPI_LED_MODE: "DPI LED Mode",
            }

        @property
        def name(self) -> str:
            return ButtonMouseFunction.Type.names()[self]

    def __init__(self, mouse: MouseData, offset: int):
        data = list(mouse.data[offset:offset + 4])
        if data in [function.value for function in ButtonMouseFunction.Type]:
            self.type = ButtonMouseFunction.Type(data)
        else:
            raise ValueError(f"Invalid MouseFunction data: {data}")
        super().__init__(mouse, offset)

    @classmethod
    def type_name(cls) -> str:
        return "Mouse Function"

    def to_raw(self) -> list[int]:
        return self.type.value

    def __str__(self) -> str:
        return f"{self.type.name}"
