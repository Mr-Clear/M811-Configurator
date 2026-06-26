'''Section that contains a list of subsections.'''

from dataclasses import dataclass, field
from typing import Any

from .section import Section
from .parent_section import AbstractParentSection


@dataclass
class ListSection(AbstractParentSection):
    length: int = 1
    subsections: list[Section] = field(default_factory=list) # type: ignore

    @classmethod
    def type_name(cls) -> str:
        return "List"

    @property
    def size(self) -> int:
        '''Get the size of the section.'''
        return self.length
    @size.setter
    def size(self, value: int) -> None:
        '''Set the size of the section.'''
        self.length = value

    def children(self) -> list[Section]:
        '''Get the child sections of this section.'''
        return self.subsections

    def add_section(self, subsection: Section) -> None:
        '''Add a subsection to the section.'''
        if subsection.relative_start < 0 or subsection.relative_end > self.size:
            raise ValueError(f"Subsection {subsection} is out of bounds of section {self}.")
        if self.get_overlaps(subsection.relative_start, subsection.size):
            raise ValueError(
                f"Subsection {subsection} overlaps with existing subsections of section {self}:" +
                ", ".join(str(s) for s in self.get_overlaps(subsection.relative_start, subsection.size)))
        self.subsections.append(subsection)
        self.subsections.sort(key=lambda s: s.relative_start)

    def fill_dict(self, d: dict[str, Any]) -> None:
        super().fill_dict(d)
        d["size"] = self.size
        d["subsections"] = [subsection.to_dict() for subsection in self.subsections]

    def __str__(self) -> str:
        return f"'{self.name} {self.size} (0x{self.relative_start:X} - 0x{self.relative_end:X})'"

    def load_from_dict(self, data: dict[str, Any]) -> None:
        '''Load the section from a dictionary.'''
        self.length = data["size"]
        self.subsections = [Section.from_dict(subsection)
                            for subsection in data.get("subsections", [])]
        for subsection in self.subsections:
            subsection.parent = self
