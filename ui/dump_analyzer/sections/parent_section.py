'''Abstract base class for sections that contain subsections.'''

from abc import ABC, abstractmethod
from dataclasses import dataclass

from ui.dump_analyzer.sections.section import Section


@dataclass
class AbstractParentSection(Section, ABC):
    @abstractmethod
    def children(self) -> list[Section]:
        pass

    def get_section_for_index(self, idx: int) -> Section | None:
        '''Get the subsection that contains the given index.'''
        for subsection in self.children():
            if subsection.contains_absolute_index(idx):
                return subsection
        return None

    def get_section_map(self) -> list[Section]:
        '''Get a list that maps indices to sections.'''
        section_map: list[Section] = [self] * self.size
        for subsection in self.children():
            for idx in range(subsection.relative_start, subsection.relative_end):
                section_map[idx - self.relative_start] = subsection
        return section_map

    def find_descendant(self, position: int) -> Section | None:
        '''Find the descendant section that contains the given position.'''
        if not self.contains_absolute_index(position):
            return None
        for subsection in self.children():
            if subsection.contains_absolute_index(position):
                if isinstance(subsection, AbstractParentSection):
                    descendant = subsection.find_descendant(position)
                    if descendant is not None:
                        return descendant
                return subsection
        return self
