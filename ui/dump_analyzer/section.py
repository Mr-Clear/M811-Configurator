''' Defines a section in the binary data. '''
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from PySide6.QtGui import QColor

if TYPE_CHECKING:
    from .section_list import SectionList

@dataclass
class Section(ABC):
    name: str
    start: int
    parent: SectionList | None = None
    color: QColor | None = None

    @classmethod
    @abstractmethod
    def type_name(cls) -> str:
        '''Get the user-friendly name of the section type.'''
        pass

    @property
    @abstractmethod
    def size(self) -> int:
        '''Get the size of the section.'''
        pass


    @property
    def end(self) -> int:
        '''Get the end of the section.'''
        return self.start + self.size

    def contains_index(self, idx: int) -> bool:
        '''Check if the section contains the given index.'''
        return self.start <= idx < self.end

    def children(self) -> list[Section]:
        '''Get the child sections of this section.'''
        return []

    def to_dict(self) -> dict[str, Any]:
        '''Convert the section to a dictionary for JSON serialization.'''
        d ={
            "type": type(self).__name__,
            "name": self.name,
            "start": self.start,
            "color": self.color.name() if self.color else None,
        }
        self.fill_dict(d)
        return d

    def overlaps_with(self, other: Section) -> bool:
        '''Check if this section overlaps with another section.'''
        if other.start < self.end and other.end > self.start:
            return True
        if other.end > self.start and other.start < self.end:
            return True
        return False

    @abstractmethod
    def load_from_dict(self, data: dict[str, Any]) -> None:
        '''Load the section from a dictionary.'''
        pass

    @abstractmethod
    def fill_dict(self, d: dict[str, Any]) -> None:
        '''Fill a dictionary with the section's data for JSON serialization.'''
        pass

    def get_overlaps(self, start: int, size: int) -> list[Section]:
        '''Get a list of children that overlap with the given start index and size.'''
        overlaps: list[Section] = []
        for child in self.children():
            if child.start < start + size and child.end > start:
                overlaps.append(child)
        return overlaps

    @property
    def root(self) -> SectionList:
        '''Get the root section of this section.'''
        if self.parent is None:
            if isinstance(self, SectionList):
                return self
            else:
                raise ValueError("Section without parent must be a SectionList.")
        return self.parent.root

    @property
    def absolute_start(self) -> int:
        '''Get the absolute start of this section.'''
        if self.parent is None:
            return self.start
        return self.parent.absolute_start + self.start

    @property
    def absolute_end(self) -> int:
        '''Get the absolute end of this section.'''
        return self.absolute_start + self.size

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Section:
        '''Create a section from a dictionary.'''
        type_name = data.get("type")
        if type_name == "SectionList":
            from .section_list import SectionList
            t = SectionList
        elif type_name == "SectionValue":
            from .section_value import SectionValue
            t = SectionValue
        else:
            raise ValueError(f"Unknown section type: {type_name}")
        s = t(name=data["name"], start=data["start"])
        s.load_from_dict(data)
        return s
