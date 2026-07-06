"""Section that repeats one subsection multiple times."""

from dataclasses import dataclass, field
from typing import Any

from ui.dump_analyzer.sections.parent_section import AbstractParentSection
from ui.dump_analyzer.sections.section import Section


@dataclass
class ArraySection(AbstractParentSection):
    child_section: Section | None = None
    repetitions: int = 1 # Number of repetitions of the child section
    gap: int = 0  # Gap between each repetition of the child section
    padding: int = 0  # Free space after the last repetition of the child section
    _children_cache_key: tuple[int, int, int, int, int] | None = field(default=None, init=False, repr=False)
    _children_cache: list[Section] = field(default_factory=list, init=False, repr=False)


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
            self._children_cache_key = None
            self._children_cache = []
            return []
        if prototype_only:
            return [self.child_section]

        key = (
            id(self.child_section),
            self.repetitions,
            self.gap,
            self.child_section.relative_start,
            self.child_section.size,
        )
        if self._children_cache_key != key:
            child = self.child_section
            children: list[Section] = [child]
            for i in range(1, self.repetitions):
                clone = Section.from_dict(child.to_dict())
                clone.parent = self
                clone.relative_start = child.relative_start + i * (child.size + self.gap)
                children.append(clone)
            self._children_cache_key = key
            self._children_cache = children
        return list(self._children_cache)

    def add_section(self, subsection: Section) -> None:
        if self.child_section is not None:
            raise ValueError(f"ArraySection {self} already has a subsection.")
        self.child_section = subsection
        self._children_cache_key = None
        self._children_cache = []

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
        self._children_cache_key = None
        self._children_cache = []
