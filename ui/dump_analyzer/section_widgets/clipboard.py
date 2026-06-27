"""Functions to copy and paste sections to and from the clipboard."""

from ..sections.section import Section


def copy_section_to_clipboard(section: Section) -> None:
    """Copy the given section to the clipboard."""
    from PySide6.QtWidgets import QApplication
    import json

    clipboard = QApplication.clipboard()
    clipboard.setText(json.dumps(section.to_dict(), indent=2))

def get_section_from_clipboard() -> Section | None:
    """Paste a section from the clipboard."""
    from PySide6.QtWidgets import QApplication
    import json

    clipboard = QApplication.clipboard()
    text = clipboard.text()
    if not text:
        return None
    try:
        data = json.loads(text)
        return Section.from_dict(data)
    except (json.JSONDecodeError, KeyError, TypeError):
        return None
