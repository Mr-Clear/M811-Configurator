
from dataclasses import dataclass
from enum import Flag, auto

from ..usb_hid import ScanCode
from ..physical_layout import PhysicalLayout

class Modifier(Flag):
    """Modifier keys that can be pressed simultaneously with other keys."""
    NONE = 0
    SHIFT = auto()
    CTRL = auto()
    ALT = auto()
    ALTGR = auto()
    NUMLK = auto()


@dataclass(frozen=True)
class LayoutKey:
    """A key in a keyboard layout, which may be mapped to multiple physical keys."""
    primary: str
    additional: dict[Modifier, str] | None = None
    is_character: bool = True
    representation: str | None = None
    is_letter: bool = False

    @property
    def labels(self) -> dict[Modifier, str]:
        """Return a dictionary mapping modifiers to the labels for this key."""
        labels: dict[Modifier, str] = {Modifier.NONE: self.primary}
        if self.additional:
            labels.update(self.additional)
        return labels

@dataclass(frozen=True)
class KeyboardLayout:
    """A keyboard layout, which maps physical keys to characters."""
    name: str
    physical_layout: PhysicalLayout
    modifiers: dict[ScanCode, Modifier]
    keys: dict[ScanCode, LayoutKey]

    @property
    def modifier_keys(self) -> dict[Modifier, set[ScanCode]]:
        """Return a dictionary mapping modifiers to the physical keys that trigger them."""
        return self.get_modifier_keys(self.modifiers)

    @staticmethod
    def get_modifier_keys(modifiers: dict[ScanCode, Modifier]) -> dict[Modifier, set[ScanCode]]:
        """Return a dictionary mapping modifiers to the physical keys that trigger them."""
        modifier_keys: dict[Modifier, set[ScanCode]] = {}
        for scan_code, modifier in modifiers.items():
            if modifier not in modifier_keys:
                modifier_keys[modifier] = set()
            modifier_keys[modifier].add(scan_code)
        return modifier_keys

f_keys = {
    ScanCode.F1: LayoutKey("F1", is_character=False),
    ScanCode.F2: LayoutKey("F2", is_character=False),
    ScanCode.F3: LayoutKey("F3", is_character=False),
    ScanCode.F4: LayoutKey("F4", is_character=False),
    ScanCode.F5: LayoutKey("F5", is_character=False),
    ScanCode.F6: LayoutKey("F6", is_character=False),
    ScanCode.F7: LayoutKey("F7", is_character=False),
    ScanCode.F8: LayoutKey("F8", is_character=False),
    ScanCode.F9: LayoutKey("F9", is_character=False),
    ScanCode.F10: LayoutKey("F10", is_character=False),
    ScanCode.F11: LayoutKey("F11", is_character=False),
    ScanCode.F12: LayoutKey("F12", is_character=False),
}

cursor_keys = {
    ScanCode.UP: LayoutKey("↑", is_character=False),
    ScanCode.DOWN: LayoutKey("↓", is_character=False),
    ScanCode.LEFT: LayoutKey("←", is_character=False),
    ScanCode.RIGHT: LayoutKey("→", is_character=False),
}

general_keys = {
    ScanCode.ESC: LayoutKey("Esc", is_character=False),
    **f_keys,
    **cursor_keys,
}

extra_f_keys = {
    ScanCode.F13: LayoutKey("F13", is_character=False),
    ScanCode.F14: LayoutKey("F14", is_character=False),
    ScanCode.F15: LayoutKey("F15", is_character=False),
    ScanCode.F16: LayoutKey("F16", is_character=False),
    ScanCode.F17: LayoutKey("F17", is_character=False),
    ScanCode.F18: LayoutKey("F18", is_character=False),
    ScanCode.F19: LayoutKey("F19", is_character=False),
    ScanCode.F20: LayoutKey("F20", is_character=False),
    ScanCode.F21: LayoutKey("F21", is_character=False),
    ScanCode.F22: LayoutKey("F22", is_character=False),
    ScanCode.F23: LayoutKey("F23", is_character=False),
    ScanCode.F24: LayoutKey("F24", is_character=False),
}

extra_keys = {
    **extra_f_keys,
}

def known_layouts() -> dict[str, KeyboardLayout]:
    """Return a dictionary of known keyboard layouts."""
    from .en_US import layout_en_us
    from .de_DE import layout_de_de
    return {
        layout_en_us.name: layout_en_us,
        layout_de_de.name: layout_de_de,
    }
