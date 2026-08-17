from ui.mouse_data import MouseData
from ui.mouse_data.button import Button


from enum import Enum


class ButtonMacro(Button):
    ''' Button that is mapped to a macro. '''
    MACRO_COUNT = 16
    MAX_REPEAT = 255

    class Type(Enum):
        REPEAT = 0x00
        HOLD = 0x80
        TOGGLE = 0x40

    def __init__(self, mouse: MouseData, offset: int):
        super().__init__(mouse, offset)

    @classmethod
    def type_name(cls) -> str:
        return "Macro"

    @classmethod
    def is_data_valid(cls, mouse: MouseData, offset: int) -> bool:
        data = list(mouse.data[offset:offset + Button.DATA_LENGTH])
        if data[0] != 0x91:
            return False
        if (data[1] & 0xF0) not in [macro_type.value for macro_type in ButtonMacro.Type]:
            return False
        macro_id = data[1] & 0x0F
        if macro_id < 0 or macro_id > ButtonMacro.MACRO_COUNT - 1:
            return False
        if (data[1] & 0xF0) == ButtonMacro.Type.REPEAT.value:
            if data[2] < 1 or data[2] > ButtonMacro.MAX_REPEAT:
                return False
        else:
            if data[2] != 0xFF or data[3] != 0xFF:
                return False
        return True

    def set_default(self) -> None:
        self.raw_data = bytes([
            0x91,
            0x00, # macro id and type
            0x01, # repeat count
            0xFF # reserved
        ])

    @property
    def macro_id(self) -> int:
        ''' The ID of the macro. '''
        return self.raw_data[1] & 0x0F
    @macro_id.setter
    def macro_id(self, macro_id: int) -> None:
        ''' Set the ID of the macro. '''
        if macro_id < 1 or macro_id > ButtonMacro.MACRO_COUNT:
            raise ValueError(f"Invalid macro ID: {macro_id}")
        data = bytearray(self.raw_data)
        data[1] = (data[1] & 0xF0) | (macro_id & 0x0F)
        self.raw_data = data

    @property
    def macro_type(self) -> Type:
        ''' The type of the macro. '''
        return ButtonMacro.Type(self.raw_data[1] & 0xF0)
    @macro_type.setter
    def macro_type(self, macro_type: Type) -> None:
        ''' Set the type of the macro. '''
        data = bytearray(self.raw_data)
        data[1] = (data[1] & 0x0F) | macro_type.value
        self.raw_data = data

    @property
    def repeat_count(self) -> int:
        ''' The repeat count of the macro. '''
        return self.raw_data[2]
    @repeat_count.setter
    def repeat_count(self, repeat_count: int) -> None:
        ''' Set the repeat count of the macro. '''
        if self.macro_type != ButtonMacro.Type.REPEAT:
            raise ValueError("Repeat count can only be set for repeat macros.")
        if repeat_count < 1 or repeat_count > ButtonMacro.MAX_REPEAT:
            raise ValueError(f"Invalid repeat count: {repeat_count}")
        data = bytearray(self.raw_data)
        data[2] = repeat_count
        self.raw_data = data

    def __str__(self) -> str:
        if self.macro_type == ButtonMacro.Type.REPEAT:
            return f'{self.macro_id} Repeat {self.repeat_count} times'
        return f'{self.macro_id} {self.macro_type.name.title()}'
