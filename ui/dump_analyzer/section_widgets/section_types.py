"""Provides all section types and their widgets."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..sections.section import Section
    from .section_widget import SectionDetailsWidgetBase

def get_section_types() -> dict[type[Section], type[SectionDetailsWidgetBase[Section]]]:
    """Get a list of all section types."""
    from ..sections.array_section import ArraySection
    from ..sections.list_section import ListSection
    from ..sections.value_section import ValueSection
    from .array_section_widget import ArraySectionWidget
    from .list_section_widget import ListSectionWidget
    from .value_section_widget import ValueSectionWidget
    return {ListSection: ListSectionWidget,
            ValueSection: ValueSectionWidget,
            ArraySection: ArraySectionWidget}
