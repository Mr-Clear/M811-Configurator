'''Section that contains a list of subsections.'''

from dataclasses import dataclass, field
from typing import Any

from ui.dump_analyzer.section import Section


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

    def get_section_for_index(self, idx: int) -> Section | None:
        '''Get the subsection that contains the given index.'''
        for subsection in self.subsections:
            if subsection.contains_absolute_index(idx):
                return subsection
        return None

    def get_section_map(self) -> list[Section]:
        '''Get a list that maps indices to sections.'''
        section_map: list[Section] = [self] * self.size
        for subsection in self.subsections:
            for idx in range(subsection.relative_start, subsection.relative_end):
                section_map[idx - self.relative_start] = subsection
        return section_map

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


    def find_descendant(self, position: int) -> Section | None:
        '''Find the descendant section that contains the given position.'''
        if not self.contains_absolute_index(position):
            return None
        for subsection in self.subsections:
            if subsection.contains_absolute_index(position):
                if isinstance(subsection, SectionList):
                    descendant = subsection.find_descendant(position)
                    if descendant is not None:
                        return descendant
                return subsection
        return self
