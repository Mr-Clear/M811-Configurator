''' Defines a section in the binary data. '''
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from PySide6.QtGui import QColor

if TYPE_CHECKING:
    from ui.redragon_mouse import ValueFunction
    from .parent_section import AbstractParentSection

@dataclass
class Section(ABC):
    name: str
    function: ValueFunction
    relative_start: int
    parent: AbstractParentSection | None = None
    color: QColor | None = None

    @property
    def id(self) -> str:
        return f'0x{self.absolute_start:04X}({self.name})'

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

    def children(self, prototype_only: bool = False) -> list[Section]:
        '''Get the child sections of this section.'''
        return []

    def to_dict(self) -> dict[str, Any]:
        '''Convert the section to a dictionary for JSON serialization.'''
        d ={
            "type": self.type_name(),
            "name": self.name,
            "function": self.function.name,
            "start": self.relative_start,
            "color": self.color.name(QColor.NameFormat.HexArgb) if self.color else None,
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
    def root(self) -> AbstractParentSection:
        '''Get the root section of this section.'''
        if self.parent is None:
            if isinstance(self, AbstractParentSection):
                return self
            else:
                raise ValueError("Section without parent must be an AbstractParentSection.")
        return self.parent.root

    @property
    def ancestors(self) -> list[AbstractParentSection]:
        '''Get a list of ancestor sections, starting with the root and ending with the parent.'''
        if self.parent is None:
            return []
        return self.parent.ancestors + [self.parent]

    @property
    def level(self) -> int:
        '''Get the level of this section in the hierarchy.'''
        if self.parent is None:
            return 0
        return self.parent.level + 1

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Section:
        from ui.redragon_mouse import ValueFunction
        '''Create a section from a dictionary.'''
        type_name = data.get("type")
        if type_name == "List":
            from .list_section import ListSection
            t = ListSection
        elif type_name == "Value":
            from .value_section import ValueSection
            t = ValueSection
        elif type_name == "Array":
            from .array_section import ArraySection
            t = ArraySection
        else:
            raise ValueError(f"Unknown section type: {type_name}")
        s = t(name=data["name"], function=ValueFunction[data["function"]], relative_start=data["start"])
        s.color = QColor(data["color"]) if data.get("color") else None
        s.load_from_dict(data)
        return s
