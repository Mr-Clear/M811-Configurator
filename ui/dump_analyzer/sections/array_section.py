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
    padding: int = 0  # Free space after the last repetition of the child section


    @classmethod
    def type_name(cls) -> str:
        return "Array"

    @property
    def size(self) -> int:
        if self.child_section is None:
            return 0
        return self.child_section.relative_start + \
               self.repetitions * (self.child_section.size + self.gap) - self.gap + \
               self.padding

    def children(self, prototype_only: bool = False) -> list[Section]:
        if self.child_section is None:
            return []
        if prototype_only:
            return [self.child_section]
        else:
            children: list[Section] = [self.child_section]
            for i in range(1, self.repetitions):
                copy = Section.from_dict(self.child_section.to_dict())
                copy.parent = self
                copy.relative_start = self.child_section.relative_start + i * (self.child_section.size + self.gap)
                children.append(copy)
            return children
    def add_section(self, subsection: Section) -> None:
        if self.child_section is not None:
            raise ValueError(f"ArraySection {self} already has a subsection.")
        self.child_section = subsection

    def fill_dict(self, d: dict[str, Any]) -> None:
        super().fill_dict(d)
        d["repetitions"] = self.repetitions
        d["gap"] = self.gap
        d["child"] = self.child_section.to_dict() if self.child_section else None
        d["padding"] = self.padding


    def __str__(self) -> str:
        return f"'{self.name} {self.size} (0x{self.relative_start:X} - 0x{self.relative_end:X})'"

    def load_from_dict(self, data: dict[str, Any]) -> None:
        '''Load the section from a dictionary.'''
        self.repetitions = data["repetitions"]
        self.gap = data["gap"]
        self.padding = data.get("padding", 0)
        self.child_section = Section.from_dict(data["child"]) if data.get("child") else None
        if self.child_section:
            self.child_section.parent = self
