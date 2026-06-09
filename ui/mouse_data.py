''' Manage all the data that is stored on the mouse. '''
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Generator

from mouse import PROFILE_COUNT as MOUSE_PROFILE_COUNT
from mouse import Mouse, MouseType
from ui.keyboard import Modifier, ScanCode
from ui.mouse_config import get_mouse_config

DPI_VALUES: dict[int, list[int]] = {
    200: [0x4, 0],
    300: [0x6, 0],
    400: [0x9, 0],
    500: [0xb, 0],
    600: [0xd, 0],
    700: [0xf, 0],
    800: [0x12, 0],
    900: [0x14, 0],
    1000: [0x16, 0],
    1100: [0x18, 0],
    1200: [0x1b, 0],
    1300: [0x1d, 0],
    1400: [0x1f, 0],
    1500: [0x21, 0],
    1600: [0x24, 0],
    1700: [0x26, 0],
    1800: [0x28, 0],
    1900: [0x2b, 0],
    2000: [0x2d, 0],
    2100: [0x2f, 0],
    2200: [0x31, 0],
    2300: [0x34, 0],
    2400: [0x36, 0],
    2500: [0x38, 0],
    2600: [0x3a, 0],
    2700: [0x3d, 0],
    2800: [0x3f, 0],
    2900: [0x41, 0],
    3000: [0x43, 0],
    3100: [0x46, 0],
    3200: [0x48, 0],
    3300: [0x4a, 0],
    3400: [0x4d, 0],
    3500: [0x4f, 0],
    3600: [0x51, 0],
    3700: [0x53, 0],
    3800: [0x56, 0],
    3900: [0x58, 0],
    4000: [0x5a, 0],
    4100: [0x5c, 0],
    4200: [0x5f, 0],
    4300: [0x61, 0],
    4400: [0x63, 0],
    4500: [0x66, 0],
    4600: [0x68, 0],
    4700: [0x6a, 0],
    4800: [0x6c, 0],
    4900: [0x6f, 0],
    5000: [0x71, 0],
    5100: [0x73, 0],
    5200: [0x75, 0],
    5300: [0x78, 0],
    5400: [0x7a, 0],
    5500: [0x7c, 0],
    5600: [0x7f, 0],
    5700: [0x81, 0],
    5800: [0x83, 0],
    5900: [0x85, 0],
    6000: [0x87, 0],
    6100: [0x8a, 0],
    6200: [0x8c, 0],
    6400: [0x48, 1],
    6600: [0x4a, 1],
    6800: [0x4d, 1],
    7000: [0x4f, 1],
    7200: [0x51, 1],
    7400: [0x53, 1],
    7600: [0x56, 1],
    7800: [0x58, 1],
    8000: [0x5a, 1],
    8200: [0x5c, 1],
    8400: [0x5f, 1],
    8600: [0x61, 1],
    8800: [0x63, 1],
    9000: [0x66, 1],
    9200: [0x68, 1],
    9400: [0x6a, 1],
    9600: [0x6c, 1],
    9800: [0x6f, 1],
    10000: [0x71, 1],
    10200: [0x73, 1],
    10400: [0x75, 1],
    10600: [0x78, 1],
    10800: [0x7a, 1],
    11000: [0x7c, 1],
    11200: [0x7f, 1],
    11400: [0x81, 1],
    11600: [0x83, 1],
    11800: [0x85, 1],
    12000: [0x87, 1],
    12200: [0x8a, 1],
    12400: [0x8c, 1],
}

PROFILE_COUNT = MOUSE_PROFILE_COUNT

class Button(ABC):
    ''' Base class for button definitions. '''

    def __init__(self, data: list[int] | None):
        ''' Creates a Button from a list of integers. '''
        if data is not None and len(data) != 4:
            raise ValueError('Button data must be a list of 4 integers.')

    @classmethod
    def from_raw(cls, data: list[int]) -> Button:
        ''' Creates a Button from a list of integers. '''
        if len(data) != 4:
            raise ValueError('Button data must be a list of 4 integers.')
        for subclass in cls.get_all_button_types():
            try:
                btn = subclass(data)
                return btn
            except ValueError:
                continue
        raise ValueError(f"Failed to decode button data: {data}")

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
        return cls.__subclasses__()

    @property
    def button_type(self) -> type[Button]:
        ''' Returns the type of the button. '''
        for button_type in Button.get_all_button_types():
            if isinstance(self, button_type):
                return button_type
        raise ValueError('Unknown button type.')

    def get_type_name(self) -> str:
        ''' Returns the name of the button type. '''
        return self.button_type.__name__

    def get_type_index(self) -> int:
        ''' Returns the index of the button type. '''
        button_types = Button.get_all_button_types()
        for index, button_type in enumerate(button_types):
            if isinstance(self, button_type):
                return index
        raise ValueError('Unknown button type.')


class ButtonOff(Button):
    ''' Button without functionality. '''

    def __init__(self, data: list[int] | None):
        if data is None:
            data = [0x00, 0x00, 0x00, 0x00]
        if len(data) != 4:
            raise ValueError('ButtonOff data must be a list of 4 integers.')
        if data != [0x00, 0x00, 0x00, 0x00]:
            raise ValueError(f"Invalid ButtonOff data: {data}")

    @classmethod
    def type_name(cls) -> str:
        return "Off"

    def to_raw(self) -> list[int]:
        return [0x00, 0x00, 0x00, 0x00]

    def __str__(self) -> str:
        return "Button Off"


class ButtonMouseButton(Button):
    ''' Button that is mapped to a mouse button. '''
    class Type(Enum):
        LEFT = 0x81
        RIGHT = 0x82
        MIDDLE = 0x83
        BACK = 0x84
        FORWARD = 0x85
        SCROLL_UP = 0x8B
        SCROLL_DOWN = 0x8C

        @property
        def name(self) -> str:
            return self._name_.replace("_", " ").title()

    def __init__(self, data: list[int] | None):
        if data is None:
            data = [ButtonMouseButton.Type.LEFT.value, 0x00, 0x00, 0x00]
        if len(data) != 4:
            raise ValueError('MouseButton data must be a list of 4 integers.')
        if data[1] != 0x00 or data[2] != 0x00 or data[3] != 0x00:
            raise ValueError(f"Invalid MouseButton data: {data}")
        if data[0] not in [button.value for button in ButtonMouseButton.Type]:
            raise ValueError(f"Invalid mouse button type: {data[0]}")
        self.mouse_button_type = ButtonMouseButton.Type(data[0])

    @classmethod
    def type_name(cls) -> str:
        return "Mouse Button"

    def to_raw(self) -> list[int]:
        return [self.mouse_button_type.value, 0x00, 0x00, 0x00]

    def __str__(self) -> str:
        return f"{self.mouse_button_type.name.title()}"


class ButtonMouseFunction(Button):
    ''' Button that is mapped to a mouse function. '''
    class Type(Enum):
        DPI_PLUS = [0x8a, 0x00, 0x00, 0x00]
        DPI_MINUS = [0x89, 0x00, 0x00, 0x00]
        SWITCH_PROFILE = [0x8d, 0x00, 0x00, 0x00]
        PROFILE_PLUS = [0x94, 0x00, 0x00, 0x00]
        PROFILE_MINUS = [0x95, 0x00, 0x00, 0x00]
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
                ButtonMouseFunction.Type.SWITCH_PROFILE: "Switch Profile",
                ButtonMouseFunction.Type.PROFILE_PLUS: "Profile+",
                ButtonMouseFunction.Type.PROFILE_MINUS: "Profile-",
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

    def __init__(self, data: list[int] | None):
        if data is None:
            data = ButtonMouseFunction.Type.DPI_PLUS.value
        if len(data) != 4:
            raise ValueError(
                'MouseFunction data must be a list of 4 integers.')
        if data in [function.value for function in ButtonMouseFunction.Type]:
            self.type = ButtonMouseFunction.Type(data)
        else:
            raise ValueError(f"Invalid MouseFunction data: {data}")

    @classmethod
    def type_name(cls) -> str:
        return "Mouse Function"

    def to_raw(self) -> list[int]:
        return self.type.value

    def __str__(self) -> str:
        return f"{self.type.name}"


class ButtonKeyPress(Button):
    ''' Button that is mapped to a keyboard key including modifiers. '''

    def __init__(self, data: list[int] | None):
        if data is None:
            data = [0x90, 0x00, ScanCode.A.value[0], 0x00]
        if len(data) != 4:
            raise ValueError('KeyPress data must be a list of 4 integers.')
        if data[0] != 0x90 and data[0] != 0x8f:
            raise ValueError(f"Invalid KeyPress data: {data}")
        self._modifiers = data[1]
        self._scan_code = data[2]
        if self._scan_code not in [scan_code.code for scan_code in ScanCode]:
            raise ValueError(f"Invalid scan code: {self._scan_code:#02x}")

    @classmethod
    def type_name(cls) -> str:
        return "Key Press"

    @property
    def key(self) -> ScanCode:
        ''' The scan code of the key press. '''
        return ScanCode.from_code(self._scan_code)
    @key.setter
    def key(self, scan_code: ScanCode) -> None:
        ''' Set the scan code of the key press. '''
        self._scan_code = scan_code.code

    @property
    def modifiers(self) -> set[Modifier]:
        ''' The modifiers of the key press. '''
        modifiers: set[Modifier] = set()
        for modifier in Modifier:
            if self._modifiers & modifier.value:
                modifiers.add(modifier)
        return modifiers

    @modifiers.setter
    def modifiers(self, modifiers: set[Modifier]) -> None:
        ''' Set the modifiers of the key press. '''
        i = 0
        for modifier in modifiers:
            i |= modifier.value
        self._modifiers = i

    def to_raw(self) -> list[int]:
        return [0x90 if self._modifiers == 0 else 0x8f, self._modifiers, self._scan_code, 0x00]

    def _modifiers_str(self) -> str:
        modifiers_str = ""
        for modifier in Modifier:
            if self._modifiers & modifier.value:
                modifiers_str += modifier.name + "+"
        return modifiers_str[:-1] if modifiers_str else ""

    def __str__(self) -> str:
        modifiers_str = self._modifiers_str()
        scan_code_str = f"{ScanCode.from_code(self._scan_code).key_name()} ({self._scan_code:#02x})"
        if modifiers_str:
            return f"{modifiers_str}+{scan_code_str}"
        else:
            return f"{scan_code_str}"


class ButtonSpecialKey(Button):
    ''' Button that is mapped to a special function. '''
    class Type(Enum):
        MEDIA_NEXT = [0x8e, 0x01, 0xb5, 0x00]
        MEDIA_PREVIOUS = [0x8e, 0x01, 0xb6, 0x00]
        MEDIA_STOP = [0x8e, 0x01, 0xb7, 0x00]
        MEDIA_PLAY_PAUSE = [0x8e, 0x01, 0xcd, 0x00]
        MEDIA_VOLUME_UP = [0x8e, 0x01, 0xe9, 0x00]
        MEDIA_VOL_DOWN = [0x8e, 0x01, 0xea, 0x00]
        MEDIA_MUTE = [0x8e, 0x01, 0xe2, 0x00]

        BROWSER_HOME = [0x8e, 0x01, 0xFF, 0x1F]
        BROWSER_BACK = [0x8e, 0x01, 0xFF, 0x20]
        BROWSER_FORWARD = [0x8e, 0x01, 0xFF, 0x21]
        BROWSER_STOP = [0x8e, 0x01, 0xFF, 0x22]
        BROWSER_REFRESH = [0x8e, 0x01, 0xFF, 0x23]
        BROWSER_SEARCH = [0x8e, 0x01, 0xFF, 0x24]
        BROWSER_FAVORITES = [0x8e, 0x01, 0xFF, 0x25]
        MAIL = [0x8e, 0x01, 0xFF, 0x26]

        @staticmethod
        def names():
            return {
                ButtonSpecialKey.Type.MEDIA_NEXT: "Next",
                ButtonSpecialKey.Type.MEDIA_PREVIOUS: "Previous",
                ButtonSpecialKey.Type.MEDIA_STOP: "Stop",
                ButtonSpecialKey.Type.MEDIA_PLAY_PAUSE: "Play/Pause",
                ButtonSpecialKey.Type.MEDIA_VOLUME_UP: "Volume Up",
                ButtonSpecialKey.Type.MEDIA_VOL_DOWN: "Volume Down",
                ButtonSpecialKey.Type.MEDIA_MUTE: "Mute",

                ButtonSpecialKey.Type.BROWSER_HOME: "Browser Home",
                ButtonSpecialKey.Type.BROWSER_BACK: "Browser Back",
                ButtonSpecialKey.Type.BROWSER_FORWARD: "Browser Forward",
                ButtonSpecialKey.Type.BROWSER_STOP: "Browser Stop",
                ButtonSpecialKey.Type.BROWSER_REFRESH: "Browser Refresh",
                ButtonSpecialKey.Type.BROWSER_SEARCH: "Browser Search",
                ButtonSpecialKey.Type.BROWSER_FAVORITES: "Browser Favorites",
                ButtonSpecialKey.Type.MAIL: "Mail",
            }

        @property
        def name(self) -> str:
            return self.names()[self]

    def __init__(self, data: list[int] | None):
        if data is None:
            data = ButtonSpecialKey.Type.MEDIA_PLAY_PAUSE.value
        if len(data) != 4:
            raise ValueError('SpecialKey data must be a list of 4 integers.')
        if data in [function.value for function in ButtonSpecialKey.Type]:
            self.type = ButtonSpecialKey.Type(data)
        else:
            raise ValueError(f"Invalid SpecialKey data: {data}")

    @classmethod
    def type_name(cls) -> str:
        return "Special Key"

    def to_raw(self) -> list[int]:
        return self.type.value

    def __str__(self) -> str:
        return f"{self.type.name}"


class ButtonMacro(Button):
    ''' Button that is mapped to a macro. '''
    MACRO_COUNT = 16
    MAX_REPEAT = 255

    class Type(Enum):
        REPEAT = 0x00
        HOLD = 0x80
        TOGGLE = 0x40

    def __init__(self, data: list[int] | None):
        if data is None:
            data = [0x91, 0x00, 0x01, 0x00]
        if len(data) != 4:
            raise ValueError('Macro data must be a list of 4 integers.')
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

class ButtonSniper(Button):
    ''' Button that sets the DPI to a predefined sniper level while held. '''

    def __init__(self, data: list[int] | None):
        if data is None:
            data = [0x9a, 0x01, 0x04, 0x04]
        if len(data) != 4:
            raise ValueError('Sniper data must be a list of 4 integers.')
        if data[0] != 0x9a:
            raise ValueError(f"Invalid Sniper data: {data}")
        self.dpi_level = [data[2], data[1] - 1]

    @classmethod
    def type_name(cls) -> str:
        return "Sniper"

    @property
    def dpi(self) -> int:
        ''' The DPI level of the sniper button. '''
        return MouseData.RawProfileData.dpi_to_int(self.dpi_level)

    def to_raw(self) -> list[int]:
        return [0x9a, self.dpi_level[1] + 1, self.dpi_level[0], self.dpi_level[0]]

    def __str__(self) -> str:
        return f'{self.dpi} DPI'

class ButtonFireKey(Button):
    ''' Presses a key repeatedly '''
    class FireMouseButton(Enum):
        LEFT = 0x81
        RIGHT = 0x82
        MIDDLE = 0x84

    def __init__(self, data: list[int] | None):
        if data is None:
            data = [0x99, 0x81, 0x03, 0x0A]
        if len(data) != 4:
            raise ValueError('FireKey data must be a list of 4 integers.')
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

    @classmethod
    def type_name(cls) -> str:
        return "Fire Key"

    def to_raw(self) -> list[int]:
        return [0x99, self.key.value
                if isinstance(self.key, ButtonFireKey.FireMouseButton)
                else self.key.code, self.repeat_count, self.delay // 10]

    def __str__(self) -> str:
        return f'({self.key.name}, times {self.repeat_count}, delay {self.delay}ms)'

class ButtomCustom(Button):
    ''' Button with a custom function defined by the user. '''
    def __init__(self, data: list[int] | None):
        if data is None:
            data = [0x00, 0x00, 0x00, 0x00]
        if len(data) != 4:
            raise ValueError('Custom button data must be a list of 4 integers.')
        self.data = data

    @classmethod
    def type_name(cls) -> str:
        return "❗Custom❗"

    def to_raw(self) -> list[int]:
        return self.data

    def __str__(self) -> str:
        return f'{self.data}'


class PollRate(Enum):
    ''' Represents the poll rate of the mouse. '''
    RATE_125HZ = 8
    RATE_250HZ = 4
    RATE_500HZ = 2
    RATE_1000HZ = 1

    def to_raw(self) -> int:
        ''' Converts the PollRate to its raw integer value. '''
        return self.value

    @staticmethod
    def from_raw(value: int) -> PollRate:
        ''' Converts a raw integer value to a PollRate. '''
        for rate in PollRate:
            if rate.value == value:
                return rate
        raise ValueError('Invalid poll rate value.')


class ProfileData:
    ''' Wrapper that represents a single profile. '''

    def __init__(self, mouse_data: MouseData.RawMouseData, profile_index: int):
        self._mouse_data = mouse_data
        self._profile_index = profile_index

    @property
    def poll_rate(self) -> PollRate:
        ''' The poll rate of the profile. '''
        return PollRate.from_raw(self._mouse_data.poll_rates[self._profile_index])

    @poll_rate.setter
    def poll_rate(self, value: PollRate):
        ''' Sets the poll rate of the profile. '''
        self._mouse_data.poll_rates[self._profile_index] = value.to_raw()

    @property
    def scroll_speed(self) -> int:
        ''' The scroll speed of the profile. '''
        return self._mouse_data.scroll_speeds[self._profile_index]

    @scroll_speed.setter
    def scroll_speed(self, value: int):
        ''' Sets the scroll speed of the profile. '''
        self._mouse_data.scroll_speeds[self._profile_index] = value

    @property
    def effects(self) -> Effect:
        ''' The effects of the profile. '''
        return Effect.from_raw(self._raw_data.effects)

    @effects.setter
    def effects(self, value: Effect):
        ''' Sets the effects of the profile. '''
        self._raw_data.effects = value.to_raw()

    @property
    def dpis(self) -> list[int]:
        ''' The DPI levels of the profile. '''
        return [MouseData.RawProfileData.dpi_to_int(dpi) for dpi in self._raw_data.dpis]

    @dpis.setter
    def dpis(self, value: list[int]):
        ''' Sets the DPI levels of the profile. '''
        self._raw_data.dpis = [
            MouseData.RawProfileData.int_to_dpi(dpi) for dpi in value]

    def get_button(self, button_index: int) -> Button:
        ''' Gets the key mapping for a given button index. '''
        if button_index < 0 or button_index >= len(self._raw_data.keymaps):
            raise ValueError('Button index out of range.')
        return Button.from_raw(self._raw_data.keymaps[button_index])

    def set_button(self, button_index: int, button: Button):
        ''' Sets the button mapping for a given button index. '''
        if button_index < 0 or button_index >= len(self._raw_data.keymaps):
            raise ValueError('Button index out of range.')
        self._raw_data.keymaps[button_index] = button.to_raw()

    def buttons(self) -> Generator[Button]:
        for button_index in range(len(self._raw_data.keymaps)):
            yield self.get_button(button_index)

    @property
    def _raw_data(self) -> MouseData.RawProfileData:
        return self._mouse_data.profiles[self._profile_index]


class Effect:
    ''' Represents a single effect on the mouse. '''
    def __init__(self, r: int, g: int, b: int, lightmode_low: int, speed: int, lightmode_high: int, brightness: int):
        self.r = r
        self.g = g
        self.b = b
        self.lightmode_low = lightmode_low
        self.speed = speed
        self.lightmode_high = lightmode_high
        self.brightness = brightness

    @classmethod
    def from_raw(cls, data: list[int]) -> Effect:
        ''' Creates an Effect from a list of integers. '''
        if len(data) != 7:
            raise ValueError('Effect data must be a list of 7 integers.')
        return cls(*data)

    def to_raw(self) -> list[int]:
        ''' Converts the Effect to a list of integers. '''
        return [self.r, self.g, self.b, self.lightmode_low, self.speed, self.lightmode_high, self.brightness]

    def __str__(self) -> str:
        ''' Returns a human-readable string representation of the effect. '''
        return f"Color: ({self.r:03}, {self.g:03}, {self.b:03}), LightModeLow: {self.lightmode_low:2}, Speed: {self.speed}, LightModeHigh: {self.lightmode_high:2}, Brightness: {self.brightness}"

class MouseData:
    ''' Manage all the data that is stored on the mouse. '''

    @dataclass
    class RawProfileData:
        effects: list[int]
        keymaps: list[list[int]]
        dpis: list[list[int]]

        @staticmethod
        def dpi_to_int(dpi: list[int]) -> int:
            ''' Converts a list of 2 integers representing the low and high bytes of a DPI level to an integer. '''
            if len(dpi) != 2:
                raise ValueError('DPI data must be a list of 2 integers.')
            for value, data in DPI_VALUES.items():
                if data == dpi:
                    return value
            raise ValueError(f"Unknown DPI value for data: {dpi}")

        @staticmethod
        def int_to_dpi(value: int) -> list[int]:
            ''' Converts an integer DPI value to a list of 2 integers representing the low and high bytes of the DPI level. '''
            if value not in DPI_VALUES:
                raise ValueError(f"Unknown DPI value: {value}")
            return DPI_VALUES[value]

    @dataclass
    class RawMouseData:
        active_pofile: int
        poll_rates: list[int]
        profiles: list[MouseData.RawProfileData]
        scroll_speeds: list[int]

        def deep_copy(self) -> MouseData.RawMouseData:
            ''' Creates a deep copy of the RawMouseData. '''
            return MouseData.RawMouseData(
                self.active_pofile,
                self.poll_rates.copy(),
                [MouseData.RawProfileData(profile.effects.copy(),
                                          profile.keymaps.copy(),
                                          profile.dpis.copy())
                 for profile in self.profiles],
                self.scroll_speeds.copy()
            )

    class Status(Enum):
        IDLE = 0
        LOADING = 1
        SAVING = 2
        NO_ACCESS = 3

    def __init__(self, mouse: Mouse, type: MouseType):
        self._mouse = mouse
        self._type = type
        self._button_count = len(get_mouse_config(type).buttons)
        self._data_on_mouse: MouseData.RawMouseData | None = None
        self._data_in_ui: MouseData.RawMouseData | None = None
        self._status: MouseData.Status = MouseData.Status.IDLE

    def load_from_mouse(self, progress_callback: Callable[[str], None] | None = None):
        ''' Loads all data from the mouse in background. '''
        if progress_callback:
            progress_callback("Loading overall data...")
        active_profile = self._mouse.get_active_profile()
        poll_rates = self._mouse.get_poll_rates()
        scroll_speeds = self._mouse.get_scroll_speeds()
        profiles: list[MouseData.RawProfileData] = []
        for profile_index in range(PROFILE_COUNT):
            if progress_callback:
                progress_callback(f"Loading profile {profile_index + 1}/{PROFILE_COUNT}...")
            effects = self._mouse.get_effects(profile_index)
            keymaps = self._mouse.get_keymap(profile_index, self._button_count)
            dpis = self._mouse.get_dpis(profile_index)
            profiles.append(MouseData.RawProfileData(effects, keymaps, dpis))
        self._data_on_mouse = MouseData.RawMouseData(active_profile,
                                                     poll_rates,
                                                     profiles,
                                                     scroll_speeds)
        self._data_in_ui = self._data_on_mouse.deep_copy()

    def save_to_mouse(self, progress_callback: Callable[[str], None] | None = None):
        ''' Saves unsaved data to the mouse in background. '''
        if self._data_in_ui is None:
            raise ValueError('No data to save.')
        if not self._data_on_mouse or self._data_in_ui.poll_rates != self._data_on_mouse.poll_rates:
            if progress_callback:
                progress_callback("Saving poll rates...")
            self._mouse.set_poll_rates(self._data_in_ui.poll_rates)
        if not self._data_on_mouse or self._data_in_ui.scroll_speeds != self._data_on_mouse.scroll_speeds:
            if progress_callback:
                progress_callback("Saving scroll speeds...")
            self._mouse.set_scroll_speeds(self._data_in_ui.scroll_speeds)
        for profile_index in range(PROFILE_COUNT):
            if not self._data_on_mouse or self._data_in_ui.profiles[profile_index] != self._data_on_mouse.profiles[profile_index]:
                if progress_callback:
                    progress_callback(f"Saving profile {profile_index + 1}/{PROFILE_COUNT}...")
                self._mouse.set_effects(profile_index, self._data_in_ui.profiles[profile_index].effects)
                self._mouse.set_keymap(profile_index, self._data_in_ui.profiles[profile_index].keymaps)
                self._mouse.set_dpis(profile_index, self._data_in_ui.profiles[profile_index].dpis)
        self._data_on_mouse = self._data_in_ui.deep_copy()

    def load_active_profile(self):
        ''' Loads the active profile index from the mouse. '''
        profile = self._mouse.get_active_profile()
        if self._data_on_mouse:
            self._data_on_mouse.active_pofile = profile
        if self._data_in_ui:
            self._data_in_ui.active_pofile = profile
        return profile

    @property
    def mouse_type(self) -> MouseType:
        ''' The type of the mouse. '''
        return self._type

    @property
    def button_count(self) -> int:
        ''' The number of buttons on the mouse. '''
        return self._button_count

    @property
    def usb_path(self) -> tuple[int, int]:
        ''' The USB path of the mouse. '''
        return (self._mouse.dev.bus if self._mouse.dev.bus is not None else -1,
                self._mouse.dev.address if self._mouse.dev.address is not None else -1)

    @property
    def usb_id(self) -> tuple[int, int]:
        ''' The USB ID of the mouse. '''
        return (self._mouse.dev.idVendor, self._mouse.dev.idProduct)

    @property
    def status(self) -> Status:
        ''' The current status of the data. '''
        return self._status

    def get_profile_data(self, profile_index: int) -> ProfileData:
        ''' Gets the data for a given profile index. '''
        if self._data_in_ui is None:
            raise ValueError('Data not loaded from mouse yet.')
        if profile_index < 0 or profile_index >= PROFILE_COUNT:
            raise ValueError('Profile index out of range.')
        return ProfileData(self._data_in_ui, profile_index)

    def data_valid(self) -> bool:
        ''' Checks if the data in the UI is valid. '''
        return self._data_on_mouse is not None

    def data_changed(self) -> bool:
        ''' Checks if the data in the UI has changed compared to the data on the mouse. '''
        return self._data_on_mouse != self._data_in_ui

    def check_integrity(self) -> bool:
        ''' Checks the integrity of the data in the UI. '''
        if not self._check_data_integrity(self._data_in_ui):
            return False
        if not self._check_data_integrity(self._data_on_mouse):
            return False
        return True

    def _check_data_integrity(self, data: MouseData.RawMouseData | None) -> bool:
        ''' Checks the integrity of the given data. '''
        if data is None:
            return False
        if data.active_pofile < 0 or data.active_pofile >= PROFILE_COUNT:
            return False
        if len(data.poll_rates) != PROFILE_COUNT:
            return False
        for poll_rate in data.poll_rates:
            if poll_rate not in [rate.value for rate in PollRate]:
                return False
        if len(data.profiles) != PROFILE_COUNT:
            return False
        if len(data.scroll_speeds) != PROFILE_COUNT:
            return False
        for scroll_speed in data.scroll_speeds:
            if scroll_speed < 1 or scroll_speed > 20:
                return False
        return True

    def _check_profile_integrity(self, profile: MouseData.RawProfileData) -> bool:
        ''' Checks the integrity of the given profile data. '''
        if len(profile.effects) != 7:
            return False
        if len(profile.keymaps) != self._button_count:
            return False
        for keymap in profile.keymaps:
            if len(keymap) != 3:
                return False
        if len(profile.dpis) != 5:
            return False
        for dpi in profile.dpis:
            if len(dpi) != 2:
                return False
        # TODO: Check if the dpi values are in the correct range

        return True

    @property
    def active_profile(self) -> int:
        ''' The active profile on the mouse. '''
        if self._data_on_mouse is None:
            raise ValueError('Data not loaded from mouse yet.')
        return self._data_on_mouse.active_pofile
