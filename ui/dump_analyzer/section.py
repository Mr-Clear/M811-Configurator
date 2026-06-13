''' Defines a section in the binary data. '''

from dataclasses import dataclass, field
from typing import Any

from PySide6.QtGui import QColor


@dataclass
class Section:
    name: str
    start: int
    size: int
    subsections: list[Section] = field(default_factory=list) # type: ignore
    color: QColor | None = None

    @property
    def end(self) -> int:
        '''Get the end of the section.'''
        return self.start + self.size

    def contains_index(self, idx: int) -> bool:
        '''Check if the section contains the given index.'''
        return self.start <= idx < self.end

    def get_overlaps(self, start: int, size: int) -> list[Section]:
        '''Get a list of subsections that overlap with the given start index and size.'''
        overlaps: list[Section] = []
        for subsection in self.subsections:
            if subsection.start < start + size and subsection.end > start:
                overlaps.append(subsection)
        return overlaps

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

    def to_dict(self) -> dict[str, Any]:
        '''Convert the section to a dictionary for JSON serialization.'''
        return {
            "name": self.name,
            "start": self.start,
            "size": self.size,
            "color": self.color.name() if self.color else None,
            "subsections": [subsection.to_dict() for subsection in self.subsections],
        }

    def __str__(self) -> str:
        return f"'{self.name} {self.size} (0x{self.start:X} - 0x{self.end:X})'"

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Section:
        '''Create a section from a dictionary.'''
        color = QColor(data["color"]) if data.get("color") else None
        subsections = [Section.from_dict(subsection)
                       for subsection in data.get("subsections", [])]
        return Section(
            name=data["name"],
            start=data["start"],
            size=data["size"],
            color=color,
            subsections=subsections,
        )
