

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING

from PySide6.QtCore import Signal

if TYPE_CHECKING:
    from ui.dump_analyzer.sections.list_section import ListSection
from ui.dump_analyzer.sections.parent_section import AbstractParentSection
from ui.dump_analyzer.sections.section import Section
from ui.dump_analyzer.sections.value_section import ValueSection

from .keyboard import Modifier, ScanCode


class ValueFunction(Enum):
    NONE = 0
    ACTIVE_MODE = 1
    BUTTON = 2
    BUTTON_LIST = 3
    DPI = 4
    DPI_LIST = 5
    EFFECT = 6
    MACRO_STEP = 7
    MACROS = 8
    MODE_COLOR = 9
    POLL_RATE = 10
    SCROLL_SPEED = 11

    def __str__(self) -> str:
        return self.name.replace("_", " ").title()

class Observable(ABC):
    changed = Signal()

    def __init__(self, mouse: MouseData):
        self._mouse = mouse
        self._mouse._register_value(self)
    
    @abstractmethod
    def to_json(self) -> dict | list | str | int | float | bool | None:
        pass

class Value(Observable):

    def __init__(self, mouse: MouseData, offset: int, length: int) -> None:
        super().__init__(mouse)
        self._offset = offset
        self._length = length

    @property
    def mouse_data(self) -> MouseData:
        return self._mouse

    @property
    def offset(self) -> int:
        return self._offset

    @property
    def length(self) -> int:
        return self._length
    
    @property
    def end_offset(self) -> int:
        return self.offset + self.length - 1

    @property
    def raw_data(self) -> memoryview:
        return self.mouse_data.data[self.offset:self.offset + self.length]
    @raw_data.setter
    def raw_data(self, value: bytes | bytearray | memoryview) -> None:
        if len(value) != self.length:
            raise ValueError(f"Data length must be {self.length}, got {len(value)}")
        self.mouse_data._set_value(self.offset, value)

    def contains_offset(self, offset: int) -> bool:
        return self.offset <= offset < self.offset + self.length
    
    def __len__(self) -> int:
        return self.length
    
class MouseData(Observable):
    """Holds a dump of the mouse memory and provides access to the values within it."""
    def __init__(self, definition: ListSection, data: bytes | bytearray | memoryview = b'') -> None:
        self.data = bytearray(data)
        self._values: list[Value] = []
        self._active_mode: ActiveMode | None = None
        self._modes: list[Mode] = []
        self._macros: list[Macro] = []
        self._parse_definition(definition)

    def _parse_definition(self, root_section: ListSection) -> None:
        """Parses the root section to find memory offsets for all values. Raises an error on inconsistencies."""
        MODE_COUNT = 5
        errors: list[str] = []

        scroll_speeds: list[ValueSection] = []
        active_mode: ValueSection | None = None

        def find_active_mode(section: Section) -> None:
            nonlocal active_mode
            if section.function == ValueFunction.ACTIVE_MODE:
                if active_mode is not None:
                    errors.append(f"Multiple sections with function ACTIVE_MODE found: {active_mode.id} and {section.id}")
                else:
                    active_mode = section
        self._walk_sections(root_section, find_active_mode)

        def find_scroll_speeds(section: Section) -> None:
            if section.function == ValueFunction.SCROLL_SPEED:
                scroll_speeds.append(section)
        self._walk_sections(root_section, find_scroll_speeds)

        if active_mode is None:
            errors.append("No section with function ACTIVE_MODE found in the mouse definition.")
        if not scroll_speeds:
            errors.append("No scroll speeds found.")
        if len(scroll_speeds) != MODE_COUNT:
            errors.append(f"Found {len(scroll_speeds)} scroll speeds but expected {MODE_COUNT}")

        if errors:
            raise ValueError("\n".join(errors))
        
        self._values.clear()
        self._modes.clear()
        self._active_mode = ActiveMode(self, active_mode.absolute_start)
        for i in range(MODE_COUNT):
            mode = Mode(self, ScrollSpeed(self, scroll_speeds[i].absolute_start))
            self._modes.append(mode)

    @property
    def data(self) -> memoryview:
        return memoryview(self._data)
    @data.setter
    def data(self, value: bytes | bytearray | memoryview) -> None:
        if self._values and self._values[-1].end_offset >= len(value):
            raise ValueError(f"New data length {len(value)} is too short for existing values, last value ends at {self._values[-1].end_offset}")
        old_data = bytes(self._data)
        self._data = bytearray(value)
        for value in self._values:
            if value.raw_data != old_data[value.offset:value.end_offset + 1]:
                value.changed.emit()

    @property
    def active_mode(self) -> ActiveMode:
        return self._active_mode
    
    def mode(self, index: int) -> Mode:
        return self._modes[index]
    
    def _set_value(self, offset: int, data: bytes | bytearray | memoryview) -> None:
        """Set the value at the given offset and length. Notifies all registered values that are changed."""
        if offset < 0 or offset + len(data) > len(self._data):
            raise ValueError(f"Offset {offset} and length {len(data)} are out of bounds for data of length {len(self._data)}")
        changed_values: list[Value] = []
        for value in self._find_values(offset, len(data)):
            value_start = value.offset
            value_end = value.end_offset + 1

            old_value_data = self._data[value_start:value_end]
            new_value_data = bytearray(old_value_data)

            overlap_start = max(value_start, offset)
            overlap_end = min(value_end, offset + len(data))
            if overlap_start < overlap_end:
                src_start = overlap_start - offset
                src_end = overlap_end - offset
                dst_start = overlap_start - value_start
                dst_end = overlap_end - value_start
                new_value_data[dst_start:dst_end] = data[src_start:src_end]

            if old_value_data != new_value_data:
                changed_values.append(value)
        self._data[offset:offset + len(data)] = data
        for value in changed_values:
            value.changed.emit()

    def _register_value(self, value: 'Value') -> None:
        """Register a new value. Raises an error if the value is out of bounds or overlaps with existing values."""
        if value.offset < 0 or value.offset + value.length > len(self._data):
            raise ValueError(f"Value at offset {value.offset} with length {value.length} is out of bounds for data of length {len(self._data)}")
        if self._find_values(value.offset, value.length):
            raise ValueError(f"Value at offset {value.offset} with length {value.length} overlaps with existing values.")
        self._values.append(value)
        self._values.sort(key=lambda v: v.offset)

    def _find_value(self, offset: int) -> 'Value | None':
        """"Use binary search to find the value that contains the given offset."""
        left = 0
        right = len(self._values) - 1
        while left <= right:
            mid = (left + right) // 2
            value = self._values[mid]
            if value.contains_offset(offset):
                return value
            elif offset < value.offset:
                right = mid - 1
            else:
                left = mid + 1
        return None
    
    def _find_values(self, offset: int, length: int) -> list['Value']:
        """Use binary search to find all values that overlap with the given range."""
        if length <= 0:
            return []

        end = offset + length
        left = 0
        right = len(self._values)

        while left < right:
            mid = (left + right) // 2
            value = self._values[mid]
            if value.end_offset < offset:
                left = mid + 1
            else:
                right = mid

        result = []
        for value in self._values[left:]:
            if value.offset >= end:
                break
            result.append(value)
        return result
    
        
    
    def _walk_sections(self, section: Section, callback: callable[[Section], None]) -> None:
        callback(section)
        if isinstance(section, AbstractParentSection):
            for child in section.children():
                self._walk_sections(child, callback)
    
    def to_json(self) -> dict:
        """Returns a JSON-serializable representation of the mouse data."""
        return {
            "active_mode": self.active_mode.to_json(),
            "modes": [mode.to_json() for mode in self._modes],
            "data": self.data.hex()
        }


class IntValue(Value):
    """Represents an integer."""
    def __init__(self, mouse: MouseData, offset: int, length: int, min: int, max: int):
        super().__init__(mouse, offset, length)
        self._min = min
        self._max = max

    @property
    def value(self) -> int:
        return self.raw_data[0]
    @value.setter
    def value(self, value: int) -> None:
        if not (self._min <= value <= self._max):
            raise ValueError(f"Value must be between {self._min} and {self._max}, got {value}")
        self._mouse._set_value(self.offset, bytes([value]))

    def to_json(self) -> dict:
        return self.value
    

class ActiveMode(IntValue):
    """Represents the active mode of the mouse."""
    def __init__(self, mouse: MouseData, offset: int):
        super().__init__(mouse, offset, 1, 1, 5)
    
class Mode(Observable):
    def __init__(self, mouse: MouseData, scroll_speed: ScrollSpeed, poll_rates: PollRates, dpis: Dpis, effects: Effects, buttons: Buttons):
        super().__init__(mouse)
        self._scroll_speed = scroll_speed
        self._scroll_speed.changed.connect(self.changed.emit)
        self._poll_rates = poll_rates
        self._poll_rates.changed.connect(self.changed.emit)
        self._dpis = dpis
        self._dpis.changed.connect(self.changed.emit)
        self._effects = effects
        self._effects.changed.connect(self.changed.emit)
        self._buttons = buttons
        self._buttons.changed.connect(self.changed.emit)
    
    def to_json(self) -> dict:
        return {
            "scroll_speed": self._scroll_speed.to_json(),
            "poll_rates": self._poll_rates.to_json(),
            "dpis": self._dpis.to_json(),
            "effects": self._effects.to_json(),
            "buttons": self._buttons.to_json(),
        }
    
class PollRate(IntValue):
    """Represents a single poll rate of the mouse."""
    def __init__(self, mouse: MouseData, offset: int):
        super().__init__(mouse, offset, 1, 0, 255)

class PollRates(Observable):
    """Represents the poll rates of the mouse."""
    def __init__(self, mouse: MouseData, offset: int):
        super().__init__(mouse)
        self._offset = offset
        self._length = 5
        self._poll_rates = [Value(mouse, offset + i, 1) for i in range(self._length)]
        for poll_rate in self._poll_rates:
            poll_rate.changed.connect(self.changed.emit)

    @property
    def poll_rates(self) -> list[int]:
        return [poll_rate.raw_data[0] for poll_rate in self._poll_rates]

    def to_json(self) -> dict:
        return {
            "poll_rates": self.poll_rates
        }

class MacroStep(Value):
    """Represents a single step of a macro."""
    def __init__(self, mouse: MouseData, offset: int):
        super().__init__(mouse, offset, 3)

    def is_active(self) -> bool:
        return self.raw_data[0] != 0x00
    
    def to_json(self) -> dict:
        return tuple(self.raw_data)
    
class Macro(Observable):
    """A single macro."""
    STEP_COUNT = 65
    def __init__(self, mouse: MouseData, steps: list[MacroStep]):
        if len(steps) != self.STEP_COUNT:
            raise ValueError(f"Macro must have {self.STEP_COUNT} steps, got {len(steps)}")
        super().__init__(mouse)
        self._steps = steps
        for step in self._steps:
            step.changed.connect(self.changed.emit)

    def step_count(self) -> int:
        for i, step in enumerate(self._steps):
            if not step.is_active():
                return i
        return len(self._steps)

    def to_json(self) -> dict:
        return [step.to_json() for step in self._steps]

class Dpi(Value):
    """Represents a single DPI setting of the mouse."""
    def __init__(self, mouse: MouseData, offset: int):
        super().__init__(mouse, offset, 2)
    
    @property
    def value(self) -> int:
        return int.from_bytes(self.raw_data, byteorder='little')
    @value.setter
    def value(self, value: int) -> None:
        if not (self._min <= value <= self._max):
            raise ValueError(f"Value must be between {self._min} and {self._max}, got {value}")
        self._mouse._set_value(self.offset, value.to_bytes(2, byteorder='little'))

    def to_json(self) -> dict:
        return self.value
    
class Dpis(Observable):
    """Represents the DPI settings"""
    def __init__(self, mouse: MouseData, dpis: list[Dpi]):
        super().__init__(mouse)
        self._dpis = dpis

    def value(self, index: int) -> int:
        return self._dpis[index].value
    def set_value(self, index: int, value: int) -> None:
        self._dpis[index].value = value

    def to_json(self) -> dict:
        return [dpis.value for dpis in self._dpis]

class ScrollSpeed(Value):
    """Represents the scroll speed of the mouse."""
    def __init__(self, mouse: MouseData, offset: int):
        super().__init__(mouse, offset, 1)

    @property
    def value(self) -> int:
        return self.raw_data[0]
    @value.setter
    def value(self, value: int) -> None:
        if not (0 <= value <= 255):
            raise ValueError(f"Scroll speed must be between 0 and 255, got {value}")
        self._mouse._set_value(self.offset, bytes([value]))

    def to_json(self) -> dict:
        return self.value
    
class Buttons(Observable):
    """All buttons for one mode."""
    def __init__(self, mouse: MouseData, buttons: list[Button]):
        super().__init__(mouse)
        self._buttons = buttons
        for button in self._buttons:
            button.changed.connect(self.changed.emit)

    def button(self, index: int) -> Button:
        return self._buttons[index]

    def to_json(self) -> dict:
        return [button.to_json() for button in self._buttons]
    
class Color(Value):
    """Represents a color setting."""
    def __init__(self, mouse: MouseData, offset: int):
        super().__init__(mouse, offset, 3)

    @property
    def rgb(self) -> tuple[int, int, int]:
        return tuple(self.raw_data)
    @rgb.setter
    def rgb(self, value: tuple[int, int, int]) -> None:
        if len(value) != 3 or any(not (0 <= v <= 255) for v in value):
            raise ValueError(f"Color must be a tuple of 3 integers between 0 and 255, got {value}")
        self._mouse._set_value(self.offset, bytes(value))

    def to_json(self) -> dict:
        return self.rgb

class Effect(Enum):
    """Represents the effect of a mode."""
    STATIC = (0, 0)
    BREATHING = (1, 0)
    WAVE = (2, 0)
    REACTIVE = (3, 0)
    RIPPLE = (4, 0)
    CYCLE = (5, 0)

    @property
    def name(self) -> str:
        return self._name_.replace("_", " ").title()

class Effects(Value):
    """Effects of a mode."""
    def __init__(self, mouse: MouseData, offset: int):
        super().__init__(mouse, offset, 1)
        self._color = Color(mouse, offset)
        self._color.changed.connect(self.changed.emit)
        self._speed = IntValue(mouse, offset + 4, 1, 0, 5)
        self._speed.changed.connect(self.changed.emit)
        self._brightness = IntValue(mouse, offset + 5, 1, 0, 3)
        self._brightness.changed.connect(self.changed.emit)

    @property
    def color(self) -> Color:
        return self._color
    
    @property
    def speed(self) -> IntValue:
        return self._speed
    
    @property
    def brightness(self) -> IntValue:
        return self._brightness
    
    @property
    def mode(self) -> Effect:
        return Effect(self.raw_data[3], self.raw_data[5])
    @mode.setter
    def mode(self, value: Effect) -> None:
        self._mouse._set_value(self.offset + 3, bytes([value.value[0]]))
        self._mouse._set_value(self.offset + 5, bytes([value.value[1]]))

    def to_json(self) -> dict:
        return {
            "mode": self.mode.name,
            "color": self.color.to_json(),
            "brightness": self.brightness.to_json(),
            "speed": self.speed.to_json()
        }


class Button(Value, ABC):
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
        raise ValueError(f"Failed to decode button data at offset {offset} with data {mouse.data[offset:offset+4].hex()}")

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

    def __init__(self, mouse: MouseData, offset: int):
        super().__init__(mouse, offset, 4)
        self._data = list(self.raw_data)
        if self._data != [0x00, 0x00, 0x00, 0x00]:
            raise ValueError(f"Invalid ButtonOff data: {self._data}")

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
        return int_to_dpi(self.dpi_level)

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



def _build_dpi_values() -> dict[int, list[int]]:
    values: dict[int, list[int]] = {}

    # 200..6200 in 100-DPI steps: low byte increases by +2, with +3 at specific steps.
    low_byte = 0x04
    values[200] = [low_byte, 0]
    plus_three_steps = {2, 6, 10, 14, 17, 21, 25, 29, 32, 36, 40, 43, 47, 51, 54, 59}
    for step, dpi in enumerate(range(300, 6300, 100), start=1):
        low_byte += 3 if step in plus_three_steps else 2
        values[dpi] = [low_byte, 0]

    # 6400..12400 in 200-DPI steps: reuse low bytes from 3200..6200 with high byte set.
    for dpi in range(6400, 12401, 200):
        base_dpi = dpi // 2
        values[dpi] = [values[base_dpi][0], 1]

    return values
DPI_VALUES: dict[int, list[int]] = _build_dpi_values()

def dpi_to_int(dpi: list[int]) -> int:
    ''' Converts a list of 2 integers representing the low and high bytes of a DPI level to an integer. '''
    if len(dpi) != 2:
        raise ValueError('DPI data must be a list of 2 integers.')
    for value, data in DPI_VALUES.items():
        if data == dpi:
            return value
    raise ValueError(f"Unknown DPI value for data: {dpi}")

def int_to_dpi(value: int) -> list[int]:
    ''' Converts an integer DPI value to a list of 2 integers representing the low and high bytes of the DPI level. '''
    if value not in DPI_VALUES:
        raise ValueError(f"Unknown DPI value: {value}")
    return DPI_VALUES[value]

