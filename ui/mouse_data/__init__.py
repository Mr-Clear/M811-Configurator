"""Classes to manage the mouse data and provide access to the values within it."""
from __future__ import annotations

from typing import Iterator

from ui.dump_analyzer.sections.list_section import ListSection
from ui.dump_analyzer.sections.parent_section import AbstractParentSection
from ui.dump_analyzer.sections.section import Section
from ui.dump_analyzer.sections.value_section import ValueSection

from .active_mode import ActiveMode
from .button import Button
from .color import Color
from .dpis import Dpi, Dpis
from .lighting import Lighting
from .macro import Macro, MacroStep
from .mode import Mode
from .observable_value import Observable, Value
from .poll_rate import PollRate
from .scroll_speed import ScrollSpeed
from .value_function import ValueFunction


class MouseData(Observable):
    """Holds a dump of the mouse memory and provides access to the values within it."""
    MODE_COUNT = 5
    BUTTON_COUNT = 20
    MACROS_COUNT = 30
    MACRO_STEP_COUNT = Macro.STEP_COUNT

    def __init__(self, definition: ListSection, data: bytes | bytearray | memoryview | None = None) -> None:
        super().__init__(self)
        self._data: bytearray = bytearray(b'\x00' * 0xFFFF)
        self._values: list[Value] = []
        self._active_mode: ActiveMode
        self._modes: list[Mode] = []
        self._macros: list[Macro] = []
        if data is not None:
            self.data = bytearray(data)
        self._parse_definition(definition)

    def _search_active_mode(self, root_section: ListSection, errors: list[str]) -> ValueSection | None:
        """Searches the root section for the ACTIVE_MODE section. Returns None if not found."""
        active_mode: ValueSection | None = None
        for section in self._walk_sections(root_section):
            if section.function == ValueFunction.ACTIVE_MODE:
                if active_mode is not None:
                    errors.append(f"Multiple sections with function ACTIVE_MODE found: {active_mode.id} and {section.id}")
                elif isinstance(section, ValueSection):
                    active_mode = section
                else:
                    errors.append(f"Section with function ACTIVE_MODE is not a ValueSection: {section.id}")
        if active_mode is None:
            errors.append("No section with function ACTIVE_MODE found in the mouse definition.")
        return active_mode

    def _search_scroll_speeds(self, root_section: ListSection, errors: list[str]) -> list[ValueSection]:
        """Searches the root section for the SCROLL_SPEED sections. Returns a list of ValueSections."""
        scroll_speeds: list[ValueSection] = []
        for section in self._walk_sections(root_section):
            if section.function == ValueFunction.SCROLL_SPEED:
                if isinstance(section, ValueSection):
                    scroll_speeds.append(section)
                else:
                    errors.append(f"Section with function SCROLL_SPEED is not a ValueSection: {section.id}")
        if len(scroll_speeds) != self.MODE_COUNT:
            errors.append(f"Found {len(scroll_speeds)} scroll speeds but expected {self.MODE_COUNT}")
        return scroll_speeds

    def _search_poll_rates(self, root_section: ListSection, errors: list[str]) -> list[ValueSection]:
        """Searches the root section for the POLL_RATE sections. Returns a list of ValueSections."""
        poll_rates: list[ValueSection] = []
        for section in self._walk_sections(root_section):
            if section.function == ValueFunction.POLL_RATE:
                if isinstance(section, ValueSection):
                    poll_rates.append(section)
                else:
                    errors.append(f"Section with function POLL_RATE is not a ValueSection: {section.id}")
        if len(poll_rates) != self.MODE_COUNT:
            errors.append(f"Found {len(poll_rates)} poll rates but expected {self.MODE_COUNT}")
        return poll_rates

    def _search_dpis(self, root_section: ListSection, errors: list[str]) -> list[AbstractParentSection]:
        """Searches the root section for the DPI_LIST sections. Returns a list of AbstractParentSections."""
        dpis: list[AbstractParentSection] = []
        for section in self._walk_sections(root_section):
            if section.function == ValueFunction.DPI_LIST:
                if isinstance(section, AbstractParentSection):
                    dpis.append(section)
                else:
                    errors.append(f"Section with function DPI_LIST is not an parent section: {section.id}")
        if len(dpis) != self.MODE_COUNT:
            errors.append(f"Found {len(dpis)} DPI lists but expected {self.MODE_COUNT}")
        for dpi in dpis:
            if len(dpi.children()) != 5:
                errors.append(f"Found {len(dpi.children())} DPIs in DPI list {dpi.id} but expected 5")
        return dpis

    def _search_mode_colors(self, root_section: ListSection, errors: list[str]) -> list[AbstractParentSection]:
        """Searches the root section for the MODE_COLOR sections. Returns a list of AbstractParentSections."""
        mode_colors: list[AbstractParentSection] = []
        for section in self._walk_sections(root_section):
            if section.function == ValueFunction.MODE_COLOR:
                if isinstance(section, AbstractParentSection):
                    mode_colors.append(section)
                else:
                    errors.append(f"Section with function MODE_COLOR is not an parent section: {section.id}")
        if len(mode_colors) != self.MODE_COUNT:
            errors.append(f"Found {len(mode_colors)} mode colors but expected {self.MODE_COUNT}")
        return mode_colors

    def _search_buttons(self, root_section: ListSection, errors: list[str]) -> list[list[ValueSection]]:
        buttons_sections: list[AbstractParentSection] = []
        for section in self._walk_sections(root_section):
            if section.function == ValueFunction.BUTTON_LIST:
                if isinstance(section, AbstractParentSection):
                    buttons_sections.append(section)
                else:
                    errors.append(f"Section with function BUTTON_LIST is not an parent section: {section.id}")
        buttons: list[list[ValueSection]] = []
        for button_section in buttons_sections:
            button_list: list[ValueSection] = []
            for child in button_section.children():
                if isinstance(child, ValueSection):
                    button_list.append(child)
                else:
                    errors.append(f"Child of BUTTON_LIST section {button_section.id} is not a ValueSection: {child.id}")
            buttons.append(button_list)
            if not len(button_list) == self.BUTTON_COUNT:
                errors.append(f"Found {len(button_list)} buttons in BUTTON_LIST section {button_section.id} but expected {self.BUTTON_COUNT}")
        if not len(buttons) == self.MODE_COUNT:
            errors.append(f"Found {len(buttons)} button lists but expected {self.MODE_COUNT}")
        return buttons

    def _search_macros(self, root_section: ListSection, errors: list[str]) -> list[list[ListSection]]:
        macro_sections: list[AbstractParentSection] = []
        for section in self._walk_sections(root_section):
            if section.function == ValueFunction.MACRO:
                if isinstance(section, AbstractParentSection):
                    macro_sections.append(section)
                else:
                    errors.append(f"Section with function MACRO is not an parent section: {section.id}")
        macros: list[list[ListSection]] = []
        for macro_section in macro_sections:
            macro_steps: list[ListSection] = []
            for child in macro_section.children():
                if isinstance(child, ListSection) and child.function == ValueFunction.MACRO_STEP:
                    macro_steps.append(child)
                else:
                    errors.append(f"Child of MACRO section {macro_section.id} is not a ListSection with function MACRO_STEP: {child.id}")
            macros.append(macro_steps)
            if not len(macro_steps) == self.MACRO_STEP_COUNT:
                errors.append(f"Found {len(macro_steps)} steps in MACRO section {macro_section.id} but expected {self.MACRO_STEP_COUNT}")
        if not len(macros) == self.MACROS_COUNT:
            errors.append(f"Found {len(macros)} macros but expected {self.MACROS_COUNT}")
        return macros

    def _parse_definition(self, root_section: ListSection) -> None:
        """Parses the root section to find memory offsets for all values. Raises an error on inconsistencies."""

        errors: list[str] = []
        active_mode = self._search_active_mode(root_section, errors)
        scroll_speeds = self._search_scroll_speeds(root_section, errors)
        poll_rates = self._search_poll_rates(root_section, errors)
        dpis = self._search_dpis(root_section, errors)
        mode_colors = self._search_mode_colors(root_section, errors)
        buttons = self._search_buttons(root_section, errors)
        macros = self._search_macros(root_section, errors)

        if errors:
            raise ValueError("\n".join(errors))
        assert active_mode is not None # for static type checking

        self._values.clear()
        self._modes.clear()
        self._active_mode = ActiveMode(self, active_mode.absolute_start)
        for i in range(self.MODE_COUNT):
            scroll_speed = ScrollSpeed(self, scroll_speeds[i].absolute_start)
            poll_rate = PollRate(self, poll_rates[i].absolute_start)
            dpi_list = [Dpi(self, c.absolute_start) for c in dpis[i].children()]
            dpis_obj = Dpis(self, dpi_list)
            effects = Lighting(self, 0x0449 + i * 8)
            button_objects: list[Button] = []
            for button in buttons[i]:
                button_objects.append(Button.from_raw(self, button.absolute_start))
            color = Color(self, mode_colors[i].absolute_start)
            mode = Mode(self, scroll_speed, poll_rate, dpis_obj, effects, button_objects, color)
            self._modes.append(mode)
        self._macros = [Macro(self, [MacroStep(self, child.absolute_start) for child in macro_steps]) for macro_steps in macros]

    @property
    def data(self) -> memoryview:
        return memoryview(self._data)
    @data.setter
    def data(self, value: bytes | bytearray | memoryview) -> None:
        if self._values and self._values[-1].end_offset >= len(value):
            raise ValueError(f"New data length {len(value)} is too short for existing values, last value ends at {self._values[-1].end_offset}")
        old_data = bytes(self._data)
        self._data = bytearray(value)
        for v in self._values:
            if v.raw_data != old_data[v.offset:v.end_offset + 1]: # type: ignore (Pylance is wrong!)
                v.changed.emit()

    @property
    def active_mode(self) -> ActiveMode:
        return self._active_mode

    def mode(self, index: int) -> Mode:
        return self._modes[index]

    def set_value(self, offset: int, data: bytes | bytearray | memoryview) -> None:
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

    def register_value(self, value: Value) -> None:
        """Register a new value. Raises an error if the value is out of bounds or overlaps with existing values."""
        if value.offset < 0 or value.offset + value.length > len(self._data):
            raise ValueError(f"Value at offset 0x{value.offset:04X} with length {value.length} is out of bounds for data of length {len(self._data)}")
        existing_values = self._find_values(value.offset, value.length)
        if existing_values:
            try:
                my_name = str(value)
            except Exception:
                my_name = f"Value at offset 0x{value.offset:04X} with length {value.length}"
            raise ValueError(f"{my_name} overlaps with existing values: {existing_values}")
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

    def _find_values(self, offset: int, length: int) -> list[Value]:
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

        result: list[Value] = []
        for value in self._values[left:]:
            if value.offset >= end:
                break
            result.append(value)
        return result



    def _walk_sections(self, section: Section) -> Iterator[Section]:
        yield section
        if isinstance(section, AbstractParentSection):
            for child in section.children():
                yield from self._walk_sections(child)

    def to_json(self) -> dict[str, object]:
        """Returns a JSON-serializable representation of the mouse data."""
        return {
            "active_mode": self.active_mode.to_json(),
            "modes": [mode.to_json() for mode in self._modes],
            "macros": [macro.to_json() for macro in self._macros],
            "data": self.data.hex()
        }
