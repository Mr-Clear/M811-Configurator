''' Defines a section in the binary data. '''
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from PySide6.QtGui import QColor


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
            "type": str(type(self)),
            "name": self.name,
            "start": self.start,
            "color": self.color.name() if self.color else None,
        }
        self.fill_dict(d)
        return d

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
            s = SectionList.from_dict(data)
        else:
            raise ValueError(f"Unknown section type: {type_name}")
        s.load_from_dict(data)
        return s


@dataclass
class SectionList(Section):
    length: int = 1
    subsections: list[Section] = field(default_factory=list) # type: ignore

    @classmethod
    def type_name(cls) -> str:
        return "Section List"

    @property
    def size(self) -> int:
        '''Get the size of the section.'''
        return self.length
    @size.setter
    def size(self, value: int) -> None:
        '''Set the size of the section.'''
        self.length = value

    @property
    def end(self) -> int:
        '''Get the end of the section.'''
        return self.start + self.size

    def children(self) -> list[Section]:
        '''Get the child sections of this section.'''
        return self.subsections

    def contains_index(self, idx: int) -> bool:
        '''Check if the section contains the given index.'''
        return self.start <= idx < self.end

    def add_section(self, subsection: Section) -> None:
        '''Add a subsection to the section.'''
        if not self.contains_index(subsection.start) or \
           not self.contains_index(subsection.end - 1):
            raise ValueError(
                f"Subsection {subsection} is out of bounds of section {self}.")
        if self.get_overlaps(subsection.start, subsection.size):
            raise ValueError(
                f"Subsection {subsection} overlaps with existing subsections of section {self}:" +
                ", ".join(str(s) for s in self.get_overlaps(subsection.start, subsection.size)))
        self.subsections.append(subsection)
        self.subsections.sort(key=lambda s: s.start)

    def get_section_for_index(self, idx: int) -> Section | None:
        '''Get the subsection that contains the given index.'''
        for subsection in self.subsections:
            if subsection.contains_index(idx):
                return subsection
        return None

    def get_section_map(self) -> list[Section]:
        '''Get a list that maps indices to sections.'''
        section_map: list[Section] = [self] * self.size
        for subsection in self.subsections:
            for idx in range(subsection.start, subsection.end):
                section_map[idx - self.start] = subsection
        return section_map

    def fill_dict(self, d: dict[str, Any]) -> None:
        super().fill_dict(d)
        d["size"] = self.size
        d["subsections"] = [subsection.to_dict() for subsection in self.subsections]

    def __str__(self) -> str:
        return f"'{self.name} {self.size} (0x{self.start:X} - 0x{self.end:X})'"

    def load_from_dict(self, data: dict[str, Any]) -> None:
        '''Load the section from a dictionary.'''
        self.length = data["size"]
        self.subsections = [Section.from_dict(subsection)
                            for subsection in data.get("subsections", [])]


