from enum import Enum

from ui.mouse_data import MouseData
from ui.mouse_data.button import Button


class ButtonMouseFunction(Button):
    ''' Button that is mapped to a mouse function. '''
    class MouseFunctionType(Enum):
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
        def names() -> dict[ButtonMouseFunction.MouseFunctionType, str]:
            T = ButtonMouseFunction.MouseFunctionType
            return {
                T.DPI_PLUS: "DPI+",
                T.DPI_MINUS: "DPI-",
                T.SWITCH_MODE: "Switch Mode",
                T.MODE_PLUS: "Mode+",
                T.MODE_MINUS: "Mode-",
                T.DPI_SWITCH: "DPI Switch",
                T.LED_SWITCH: "LED Switch",
                T.POLL_RATE_PLUS: "Poll Rate+",
                T.POLL_RATE_MINUS: "Poll Rate-",
                T.RESET_SETTINGS: "Reset Settings",
                T.DPI_LED_MODE: "DPI LED Mode",
            }

        @property
        def name(self) -> str:
            return ButtonMouseFunction.MouseFunctionType.names()[self]

    def __init__(self, mouse: MouseData, offset: int):
        super().__init__(mouse, offset)

    @classmethod
    def type_name(cls) -> str:
        return "Mouse Function"

    @classmethod
    def is_data_valid(cls, mouse: MouseData, offset: int) -> bool:
        data = list(mouse.data[offset:offset + Button.DATA_LENGTH])
        return data in [function.value for function in ButtonMouseFunction.MouseFunctionType]

    def set_default(self) -> None:
        self.raw_data = bytes(ButtonMouseFunction.MouseFunctionType.SWITCH_MODE.value)

    @property
    def function_type(self) -> MouseFunctionType:
        return ButtonMouseFunction.MouseFunctionType(list(self.raw_data))
    @function_type.setter
    def function_type(self, value: MouseFunctionType) -> None:
        self.raw_data = bytes(value.value)

    def __str__(self) -> str:
        return f"{self.function_type.name}"
