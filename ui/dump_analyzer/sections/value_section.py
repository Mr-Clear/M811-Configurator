'''Represents a single integer value'''

from dataclasses import dataclass
from typing import Any

from .section import Section


@dataclass
class ValueSection(Section):
    byte_count: int = 1
    min_value: int = 0
    max_value: int = 0xFF

    @classmethod
    def type_name(cls) -> str:
        return "Value"

    @property
    def size(self) -> int:
        '''Get the size of the section.'''
        return self.byte_count

    def load_from_dict(self, data: dict[str, Any]) -> None:
        '''Load the section from a dictionary.'''
        self.byte_count = data.get("length", 0)
        self.min_value = data.get("min_value", 0)
        self.max_value = data.get("max_value", 0xFF)

    def fill_dict(self, d: dict[str, Any]) -> None:
        '''Fill the dictionary with the section information for JSON serialization.'''
        d["length"] = self.byte_count
        d["min_value"] = self.min_value
        d["max_value"] = self.max_value
