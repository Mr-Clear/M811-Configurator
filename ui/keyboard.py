''' USB HID keyboard scan codes and modifiers. '''

from enum import Enum

class Modifier(Enum):
    LCtrl = 0x01
    LShift = 0x02
    LAlt = 0x04
    LWin = 0x08
    RCtrl = 0x10
    RShift = 0x20
    RAlt = 0x40
    RWin = 0x80

class Layout(Enum):
    US = 0,
    DE = 1

class ScanCode(Enum):
    A = (0x04, "A")
    B = (0x05, "B")
    C = (0x06, "C")
    D = (0x07, "D")
    E = (0x08, "E")
    F = (0x09, "F")
    G = (0x0A, "G")
    H = (0x0B, "H")
    I = (0x0C, "I")
    J = (0x0D, "J")
    K = (0x0E, "K")
    L = (0x0F, "L")
    M = (0x10, "M")
    N = (0x11, "N")
    O = (0x12, "O")
    P = (0x13, "P")
    Q = (0x14, "Q")
    R = (0x15, "R")
    S = (0x16, "S")
    T = (0x17, "T")
    U = (0x18, "U")
    V = (0x19, "V")
    W = (0x1A, "W")
    X = (0x1B, "X")
    Y = (0x1C, "Y")
    Z = (0x1D, "Z")
    # Number row
    N1 = (0x1E, "1")
    N2 = (0x1F, "2")
    N3 = (0x20, "3")
    N4 = (0x21, "4")
    N5 = (0x22, "5")
    N6 = (0x23, "6")
    N7 = (0x24, "7")
    N8 = (0x25, "8")
    N9 = (0x26, "9")
    N0 = (0x27, "0")
    # Special keys
    Enter = (0x28, "Enter")
    Escape = (0x29, "Escape")
    Backspace = (0x2A, "Backspace")
    Tab = (0x2B, "Tab")
    Space = (0x2C, "␣")
    Minus = (0x2D, "-")
    Equal = (0x2E, "=")
    LeftBracket = (0x2F, "[")
    RightBracket = (0x30, "]")
    Backslash = (0x31, "\\")
    NonUSHash = (0x32, "#")
    Semicolon = (0x33, ";")
    Apostrophe = (0x34, "'")
    Grave = (0x35, "`")
    Comma = (0x36, ",")
    Period = (0x37, ".")
    Slash = (0x38, "/")
    CapsLock = (0x39, "CapsLock")
    # Function keys
    F1 = (0x3A, "F1")
    F2 = (0x3B, "F2")
    F3 = (0x3C, "F3")
    F4 = (0x3D, "F4")
    F5 = (0x3E, "F5")
    F6 = (0x3F, "F6")
    F7 = (0x40, "F7")
    F8 = (0x41, "F8")
    F9 = (0x42, "F9")
    F10 = (0x43, "F10")
    F11 = (0x44, "F11")
    F12 = (0x45, "F12")
    # Navigation / editing cluster
    PrintScreen = (0x46, "PrintScreen")
    ScrollLock = (0x47, "ScrollLock")
    Pause = (0x48, "Pause")
    Insert = (0x49, "Insert")
    Home = (0x4A, "Home")
    PageUp = (0x4B, "PageUp")
    Delete = (0x4C, "Delete")
    End = (0x4D, "End")
    PageDown = (0x4E, "PageDown")
    RightArrow = (0x4F, "→")
    LeftArrow = (0x50, "←")
    DownArrow = (0x51, "↓")
    UpArrow = (0x52, "↑")
    # Numpad
    NumLock = (0x53, "NumLock")
    NumpadDivide = (0x54, "Num/")
    NumpadMultiply = (0x55, "Num*")
    NumpadMinus = (0x56, "Num-")
    NumpadPlus = (0x57, "Num+")
    NumpadEnter = (0x58, "NumEnter")
    Numpad1 = (0x59, "Num1")
    Numpad2 = (0x5A, "Num2")
    Numpad3 = (0x5B, "Num3")
    Numpad4 = (0x5C, "Num4")
    Numpad5 = (0x5D, "Num5")
    Numpad6 = (0x5E, "Num6")
    Numpad7 = (0x5F, "Num7")
    Numpad8 = (0x60, "Num8")
    Numpad9 = (0x61, "Num9")
    Numpad0 = (0x62, "Num0")
    NumpadPeriod = (0x63, "Num.")
    # Extra keys
    NonUSBackslash = (0x64, "\\")
    Application = (0x65, "Application")
    Power = (0x66, "Power")
    NumpadEqual = (0x67, "NumpadEqual")
    F13 = (0x68, "F13")
    F14 = (0x69, "F14")
    F15 = (0x6A, "F15")
    F16 = (0x6B, "F16")
    F17 = (0x6C, "F17")
    F18 = (0x6D, "F18")
    F19 = (0x6E, "F19")
    F20 = (0x6F, "F20")
    F21 = (0x70, "F21")
    F22 = (0x71, "F22")
    F23 = (0x72, "F23")
    F24 = (0x73, "F24")
    # Media / consumer keys (HID usage page 0x07)
    Mute = (0x7F, "Mute")
    VolumeUp = (0x80, "VolumeUp")
    VolumeDown = (0x81, "VolumeDown")
    # Modifier keys (usage page 0x07, 0xE0–0xE7)
    LCtrl = (0xE0, "LCtrl")
    LShift = (0xE1, "LShift")
    LAlt = (0xE2, "LAlt")
    LWin = (0xE3, "LWin")
    RCtrl = (0xE4, "RCtrl")
    RShift = (0xE5, "RShift")
    RAlt = (0xE6, "RAlt")
    RWin = (0xE7, "RWin")

    @property
    def code(self) -> int:
        return self.value[0]

    def key_name(self, layout: Layout = Layout.US) -> str:
        if layout in LAYOUT_RELATED_KEY_NAMES and self in LAYOUT_RELATED_KEY_NAMES[layout]:
            return LAYOUT_RELATED_KEY_NAMES[layout][self]
        return self.value[1]

    @classmethod
    def from_code(cls, code: int) -> 'ScanCode':
        for scan_code in cls:
            if scan_code.code == code:
                return scan_code
        raise ValueError(f"Unknown scan code: {code}")


LAYOUT_RELATED_KEY_NAMES: dict[Layout, dict[ScanCode, str]] = {
    Layout.US: {},
    Layout.DE: {
        ScanCode.Y: "Z",
        ScanCode.Z: "Y",
        ScanCode.LeftBracket: "Ü",
        ScanCode.RightBracket: "+",
        ScanCode.Backslash: "#",
        ScanCode.Semicolon: "Ö",
        ScanCode.Apostrophe: "Ä",
        ScanCode.NonUSBackslash: "<",
        ScanCode.Grave: "^",
        ScanCode.Minus: "ß",
        ScanCode.Equal: "´",
        ScanCode.Slash: "-",
    },
}
