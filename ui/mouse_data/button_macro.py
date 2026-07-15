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
        data = list(mouse.data[offset:offset + 4])
        if data[0] != 0x91:
            raise ValueError(f"Invalid Macro data: {data}")
        if (data[1] & 0xF0) not in [macro_type.value for macro_type in ButtonMacro.Type]:
            raise ValueError(f"Invalid macro type: {data[1] & 0xF0:#02x}")
        self.macro_id = data[1] & 0x0F
        self.macro_type = ButtonMacro.Type(data[1] & 0xF0)
        self.repeat_count = data[2]
        if self.macro_type == ButtonMacro.Type.REPEAT:
            if self.repeat_count == 0 or self.repeat_count > 20:
                raise ValueError(
                    f"Invalid repeat count for macro: {self.repeat_count}")
        else:
            if data[2] != 0xFF or data[3] != 0xFF:
                raise ValueError(f"Invalid Macro data: {data}")
        super().__init__(mouse, offset)

    @classmethod
    def type_name(cls) -> str:
        return "Macro"

    @property
    def id(self) -> int:
        ''' The ID of the macro. '''
        return self.macro_id
    @id.setter
    def id(self, macro_id: int) -> None:
        ''' Set the ID of the macro. '''
        if macro_id < 1 or macro_id > ButtonMacro.MACRO_COUNT:
            raise ValueError(f"Invalid macro ID: {macro_id}")
        self.macro_id = macro_id

    @property
    def type(self) -> Type:
        ''' The type of the macro. '''
        return self.macro_type
    @type.setter
    def type(self, macro_type: Type) -> None:
        ''' Set the type of the macro. '''
        self.macro_type = macro_type

    @property
    def repeat(self) -> int:
        ''' The repeat count of the macro. '''
        return self.repeat_count
    @repeat.setter
    def repeat(self, repeat_count: int) -> None:
        ''' Set the repeat count of the macro. '''
        if self.macro_type != ButtonMacro.Type.REPEAT:
            raise ValueError("Repeat count can only be set for repeat macros.")
        if repeat_count < 1 or repeat_count > ButtonMacro.MAX_REPEAT:
            raise ValueError(f"Invalid repeat count: {repeat_count}")
        self.repeat_count = repeat_count

    def to_raw(self) -> list[int]:
        return [0x91, self.macro_id | self.macro_type.value, 0x00, 0x00]

    def __str__(self) -> str:
        if self.macro_type == ButtonMacro.Type.REPEAT:
            return f'{self.macro_id} Repeat {self.repeat_count} times'
        return f'{self.macro_id} {self.macro_type.name.title()}'
