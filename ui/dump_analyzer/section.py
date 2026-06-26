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
    relative_start: int
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
    def relative_end(self) -> int:
        '''Get the end of the section relative to its parent.'''
        return self.relative_start + self.size - 1

    @property
    def absolute_start(self) -> int:
        '''Get the absolute start of this section.'''
        if self.parent is None:
            return self.relative_start
        return self.parent.absolute_start + self.relative_start
    @absolute_start.setter
    def absolute_start(self, value: int) -> None:
        '''Set the absolute start of this section.'''
        if self.parent is None:
            self.relative_start = value
        else:
            self.relative_start = value - self.parent.absolute_start
    @property
    def absolute_end(self) -> int:
        '''Get the absolute end of this section.'''
        return self.absolute_start + self.size - 1

    def contains_absolute_index(self, idx: int) -> bool:
        '''Check if the section contains the given index.'''
        return self.absolute_start <= idx <= self.absolute_end

    def children(self) -> list[Section]:
        '''Get the child sections of this section.'''
        return []

    def to_dict(self) -> dict[str, Any]:
        '''Convert the section to a dictionary for JSON serialization.'''
        d ={
            "type": type(self).__name__,
            "name": self.name,
            "start": self.relative_start,
            "color": self.color.name() if self.color else None,
        }
        self.fill_dict(d)
        return d

    def overlaps_with(self, other: Section) -> bool:
        '''Check if this section overlaps with another section.'''
        if other.absolute_start < self.absolute_end and other.absolute_end > self.absolute_start:
            return True
        if other.absolute_end > self.absolute_start and other.absolute_start < self.absolute_end:
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
            if child.absolute_start < start + size and child.absolute_end > start:
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
    def ancestors(self) -> list[SectionList]:
        '''Get a list of ancestor sections, starting with the root and ending with the parent.'''
        if self.parent is None:
            return []
        return self.parent.ancestors + [self.parent]

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
        s = t(name=data["name"], relative_start=data["start"])
        s.color = QColor(data["color"]) if data.get("color") else None
        s.load_from_dict(data)
        return s
