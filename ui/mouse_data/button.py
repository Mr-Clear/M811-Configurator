from abc import abstractmethod
from typing import TYPE_CHECKING

from ui.mouse_data.observable_value import Value

if TYPE_CHECKING:
    from . import MouseData

class Button(Value):
    ''' Base class for button definitions. '''

    def __init__(self, mouse: MouseData, offset: int):
        super().__init__(mouse, offset, 4)
        self._data = list(self.raw_data)

    @classmethod
    def from_raw(cls, mouse: MouseData, offset: int) -> Button:
        ''' Creates a Button from the raw data at the given offset. '''
        for subclass in cls.get_all_button_types():
            try:
                btn = subclass(mouse, offset)
                return btn
            except ValueError:
                continue
        raise ValueError(f"Failed to decode button data at offset 0x{offset:04X} with data {mouse.data[offset:offset+4].hex()}")

    @classmethod
    @abstractmethod
    def type_name(cls) -> str:
        ''' Returns the name of the button type. '''
        pass

    @abstractmethod
    def to_raw(self) -> list[int]:
        ''' Converts the Button to a raw data as used by the mouse module. '''
        pass

    @abstractmethod
    def __str__(self) -> str:
        ''' Returns a human-readable string representation of the button. '''
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
            ButtonCustom,
            ButtonFireKey,
            ButtonKeyPress,
            ButtonMacro,
            ButtonMouseButton,
            ButtonMouseFunction,
            ButtonOff,
            ButtonSniper,
            ButtonSpecialKey,
        ]

    @property
    def button_type(self) -> type[Button]:
        ''' Returns the type of the button. '''
        for button_type in Button.get_all_button_types():
            if type(self) is button_type:
                return button_type
        raise ValueError('Unknown button type.')

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

    def to_json(self) -> dict[str, object]:
        ''' Returns a JSON-serializable representation of the button. '''
        return {
            "type": self.get_type_name(),
            "data": self.to_raw()
        }
