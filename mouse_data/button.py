from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

from mouse_data.observable_value import Value

if TYPE_CHECKING:
    from . import MouseData

class Button(Value):
    ''' Base class for button definitions. '''
    DATA_LENGTH = 4

    def __init__(self, mouse: MouseData, offset: int):
        super().__init__(mouse, offset, Button.DATA_LENGTH)
        self._data = list(self.raw_data)
        self.changed.connect(self._update_type)

    @classmethod
    def from_raw(cls, mouse: MouseData, offset: int) -> Button:
        ''' Creates a Button from the raw data at the given offset. '''
        subclass = cls.type_from_raw(mouse, offset)
        if subclass is None:
            raise ValueError(f"Failed to decode button data at offset 0x{offset:04X} with data {mouse.data[offset:offset+Button.DATA_LENGTH].hex()}")
        return subclass(mouse, offset)

    @classmethod
    def is_data_valid(cls, mouse: MouseData, offset: int) -> bool:
        ''' Checks if the raw data at the given offset is valid for this button type. '''
        raise NotImplementedError("is_data_valid must be implemented in subclasses.")

    @classmethod
    def type_from_raw(cls, mouse: MouseData, offset: int) -> type[Button] | None:
        ''' Returns the button type from the raw data. '''
        for subclass in cls.get_all_button_types():
            if subclass.is_data_valid(mouse, offset):
                return subclass
        return None

    @classmethod
    @abstractmethod
    def type_name(cls) -> str:
        ''' Returns the name of the button type. '''
        pass

    @abstractmethod
    def __str__(self) -> str:
        ''' Returns a human-readable string representation of the button. '''
        pass

    @abstractmethod
    def set_default(self) -> None:
        ''' Sets the button data to its default value. '''
        pass

    @classmethod
    def get_all_button_types(cls) -> list[type[Button]]:
        ''' Returns a list of all button types. '''
        from .button_custom import ButtonCustom
        from .button_fire_key import ButtonFireKey
        from .button_key_press import ButtonKeyPress
        from .button_macro import ButtonMacro
        from .button_mouse_button import ButtonMouseButton
        from .button_mouse_function import ButtonMouseFunction
        from .button_off import ButtonOff
        from .button_sniper import ButtonSniper
        from .button_special_key import ButtonSpecialKey
        return [
            ButtonMouseButton,
            ButtonMouseFunction,
            ButtonKeyPress,
            ButtonSpecialKey,
            ButtonMacro,
            ButtonFireKey,
            ButtonSniper,
            ButtonOff,
            ButtonCustom,
        ]

    @property
    def button_type(self) -> type[Button]:
        ''' Returns the type of the button. '''
        return type(self)

    def get_type_name(self) -> str:
        ''' Returns the name of the button type. '''
        return self.button_type.__name__

    def get_type_index(self) -> int:
        ''' Returns the index of the button type. '''
        button_types = Button.get_all_button_types()
        for index, button_type in enumerate(button_types):
            if type(self) is button_type:
                return index
        raise ValueError('Unknown button type.')

    def _update_type(self) -> bool:
        t = Button.type_from_raw(self.mouse_data, self.offset)
        if t is None:
            raise ValueError(f"Failed to determine button type at offset 0x{self.offset:04X} with data {self.raw_data.hex()}")
        if type(self) is not t:
            self.__class__ = t # type: ignore
            return True
        return False

    def to_json(self) -> dict[str, object]:
        ''' Returns a JSON-serializable representation of the button. '''
        return {
            "type": self.get_type_name(),
            "data": self.raw_data.hex()
        }
