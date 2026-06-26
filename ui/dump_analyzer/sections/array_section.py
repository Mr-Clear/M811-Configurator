"""Section that repeats one subsection multiple times."""

from dataclasses import dataclass
from typing import Any

from ui.dump_analyzer.sections.parent_section import AbstractParentSection
from ui.dump_analyzer.sections.section import Section


@dataclass
class ArraySection(AbstractParentSection):
    child_section: Section | None = None
    repetitions: int = 1 # Number of repetitions of the child section
    gap: int = 0  # Gap between each repetition of the child section


    @classmethod
    def type_name(cls) -> str:
        return "Array"

    @property
    def size(self) -> int:
        return self.repetitions * (self.child_section.size if self.child_section else 0)

    def children(self) -> list[Section]:
        return [self.child_section] if self.child_section else []

    def add_section(self, subsection: Section) -> None:
        if self.child_section is not None:
            raise ValueError(f"ArraySection {self} already has a subsection.")
        self.child_section = subsection

    def fill_dict(self, d: dict[str, Any]) -> None:
        super().fill_dict(d)
        d["repetitions"] = self.repetitions
        d["gap"] = self.gap
        d["child_section"] = self.child_section.to_dict() if self.child_section else None


    def __str__(self) -> str:
        return f"'{self.name} {self.size} (0x{self.relative_start:X} - 0x{self.relative_end:X})'"

    def load_from_dict(self, data: dict[str, Any]) -> None:
        '''Load the section from a dictionary.'''
        self.repetitions = data["repetitions"]
        self.gap = data["gap"]
        self.child_section = Section.from_dict(data["child_section"]) if data.get("child_section") else None
        if self.child_section:
            self.child_section.parent = self
