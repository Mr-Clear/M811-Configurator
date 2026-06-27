'''Abstract base class for sections that contain subsections.'''

from abc import ABC, abstractmethod
from dataclasses import dataclass

from ui.dump_analyzer.sections.section import Section


@dataclass
class AbstractParentSection(Section, ABC):
    @abstractmethod
    def children(self, prototype_only: bool = False) -> list[Section]:
        pass

    def get_sections_for_index(self, idx: int) -> list[Section]:
        '''Get all sections that contain the given index.'''
        sections: list[Section] = []
        for subsection in self.children():
            if subsection.contains_absolute_index(idx):
                sections.append(subsection)
                if isinstance(subsection, AbstractParentSection):
                    sections.extend(subsection.get_sections_for_index(idx))
        return sections
