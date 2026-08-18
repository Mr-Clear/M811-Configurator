from ui.keyboard.layouts import KeyboardLayout, LayoutKey, Modifier
from ui.keyboard.physical_layout import PhysicalLayout
from ui.keyboard.usb_hid import ScanCode

from .en_US import layout_en_us

layout_de_de = KeyboardLayout(
    name="de-DE",
    physical_layout=PhysicalLayout.ISO,
    modifiers={
        ScanCode.LEFTSHIFT: Modifier.SHIFT,
        ScanCode.RIGHTSHIFT: Modifier.SHIFT,
        ScanCode.RIGHTALT: Modifier.ALTGR,
    },
    keys={
        **layout_en_us.keys,

        ScanCode.PRINT: LayoutKey("Drucken", is_character=False),
        ScanCode.SCROLLLOCK: LayoutKey("Rollen", is_character=False),
        ScanCode.PAUSE: LayoutKey("Pause", is_character=False),

        ScanCode.GRAVE: LayoutKey("^", {Modifier.SHIFT: "°"}),
        ScanCode.TWO: LayoutKey("2", {Modifier.SHIFT: '"'}),
        ScanCode.THREE: LayoutKey("3", {Modifier.SHIFT: "§"}),
        ScanCode.SIX: LayoutKey("6", {Modifier.SHIFT: "&"}),
        ScanCode.SEVEN: LayoutKey("7", {Modifier.SHIFT: "/", Modifier.ALTGR: "{"}),
        ScanCode.EIGHT: LayoutKey("8", {Modifier.SHIFT: "(", Modifier.ALTGR: "["}),
        ScanCode.NINE: LayoutKey("9", {Modifier.SHIFT: ")", Modifier.ALTGR: "]"}),
        ScanCode.ZERO: LayoutKey("0", {Modifier.SHIFT: "=", Modifier.ALTGR: "}"}),
        ScanCode.MINUS: LayoutKey("ß", {Modifier.SHIFT: "?", Modifier.ALTGR: "\\"}),
        ScanCode.EQUAL: LayoutKey("´", {Modifier.SHIFT: "`"}),
        ScanCode.Q: LayoutKey("q", {Modifier.SHIFT: "Q", Modifier.ALTGR: "@"}),
        ScanCode.E: LayoutKey("e", {Modifier.SHIFT: "E", Modifier.ALTGR: "€"}),
        ScanCode.Y: LayoutKey("z", {Modifier.SHIFT: "Z"}),
        ScanCode.LEFTBRACE: LayoutKey("ü", {Modifier.SHIFT: "Ü"}),
        ScanCode.RIGHTBRACE: LayoutKey("+", {Modifier.SHIFT: "*", Modifier.ALTGR: "~"}),
        ScanCode.SEMICOLON: LayoutKey("ö", {Modifier.SHIFT: "Ö"}),
        ScanCode.APOSTROPHE: LayoutKey("ä", {Modifier.SHIFT: "Ä"}),
        ScanCode.HASHTILDE_ISO: LayoutKey("#", {Modifier.SHIFT: "'"}),
        ScanCode.BACKSLASH_ISO: LayoutKey("<", {Modifier.SHIFT: ">", Modifier.ALTGR: "|"}),
        ScanCode.Z: LayoutKey("y", {Modifier.SHIFT: "Y"}),
        ScanCode.M: LayoutKey("m", {Modifier.SHIFT: "M", Modifier.ALTGR: "µ"}),
        ScanCode.COMMA: LayoutKey(",", {Modifier.SHIFT: ";"}),
        ScanCode.DOT: LayoutKey(".", {Modifier.SHIFT: ":"}),
        ScanCode.SLASH: LayoutKey("-", {Modifier.SHIFT: "_"}),

        ScanCode.LEFTCTRL: LayoutKey("Strg", is_character=False),
        ScanCode.RIGHTALT: LayoutKey("AltGr", is_character=False),
        ScanCode.PROPS: LayoutKey("Menü", is_character=False),
        ScanCode.RIGHTCTRL: LayoutKey("Strg", is_character=False),

        ScanCode.INSERT: LayoutKey("Einfg", is_character=False),
        ScanCode.HOME: LayoutKey("Pos1", is_character=False),
        ScanCode.PAGEUP: LayoutKey("Bild↑", is_character=False),
        ScanCode.DELETE: LayoutKey("Entf", is_character=False),
        ScanCode.END: LayoutKey("Ende", is_character=False),
        ScanCode.PAGEDOWN: LayoutKey("Bild↓", is_character=False),

        ScanCode.KP7: LayoutKey("7", {Modifier.NUMLK: "Pos1"}, representation="⑦"),
        ScanCode.KP9: LayoutKey("9", {Modifier.NUMLK: "Bild↑"}, representation="⑨"),
        ScanCode.KP1: LayoutKey("1", {Modifier.NUMLK: "Ende"}, representation="①"),
        ScanCode.KP3: LayoutKey("3", {Modifier.NUMLK: "Bild↓"}, representation="③"),
        ScanCode.KP0: LayoutKey("0", {Modifier.NUMLK: "Einfg"}, representation="⓪"),
        ScanCode.KPDOT: LayoutKey(",", {Modifier.NUMLK: "Entf"}, representation="⨀"),
    },
)
