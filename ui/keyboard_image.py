"""A self-contained PySide6 keyboard-layout renderer.

Run this file directly to open the demo application:
    python ui/keyboard_image.py
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from enum import Enum, Flag, auto

from PySide6.QtCore import QEvent, QPointF, QRectF, Qt
from PySide6.QtGui import (QColor, QFont, QMouseEvent, QPainter, QPainterPath,
                           QPaintEvent, QPen)
from PySide6.QtWidgets import (QApplication, QComboBox, QDockWidget,
                               QHBoxLayout, QMainWindow, QWidget)


class ScanCode(Enum):
    """USB HID keyboard usage (scan) codes."""
    A = 0x04    # Keyboard a and A
    B = 0x05    # Keyboard b and B
    C = 0x06    # Keyboard c and C
    D = 0x07    # Keyboard d and D
    E = 0x08    # Keyboard e and E
    F = 0x09    # Keyboard f and F
    G = 0x0a    # Keyboard g and G
    H = 0x0b    # Keyboard h and H
    I = 0x0c    # Keyboard i and I
    J = 0x0d    # Keyboard j and J
    K = 0x0e    # Keyboard k and K
    L = 0x0f    # Keyboard l and L
    M = 0x10    # Keyboard m and M
    N = 0x11    # Keyboard n and N
    O = 0x12    # Keyboard o and O
    P = 0x13    # Keyboard p and P
    Q = 0x14    # Keyboard q and Q
    R = 0x15    # Keyboard r and R
    S = 0x16    # Keyboard s and S
    T = 0x17    # Keyboard t and T
    U = 0x18    # Keyboard u and U
    V = 0x19    # Keyboard v and V
    W = 0x1a    # Keyboard w and W
    X = 0x1b    # Keyboard x and X
    Y = 0x1c    # Keyboard y and Y
    Z = 0x1d    # Keyboard z and Z

    ONE = 0x1e    # Keyboard 1 and !
    TWO = 0x1f    # Keyboard 2 and @
    THREE = 0x20    # Keyboard 3 and #
    FOUR = 0x21    # Keyboard 4 and $
    FIVE = 0x22    # Keyboard 5 and %
    SIX = 0x23    # Keyboard 6 and ^
    SEVEN = 0x24    # Keyboard 7 and &
    EIGHT = 0x25    # Keyboard 8 and *
    NINE = 0x26    # Keyboard 9 and (
    ZERO = 0x27    # Keyboard 0 and )

    ENTER = 0x28    # Keyboard Return (ENTER)
    ESC = 0x29    # Keyboard ESCAPE
    BACKSPACE = 0x2a    # Keyboard DELETE (Backspace)
    TAB = 0x2b    # Keyboard Tab
    SPACE = 0x2c    # Keyboard Spacebar
    MINUS = 0x2d    # Keyboard - and _
    EQUAL = 0x2e    # Keyboard = and +
    LEFTBRACE = 0x2f    # Keyboard [ and {
    RIGHTBRACE = 0x30    # Keyboard ] and }
    BACKSLASH_ANSI = 0x31    # Keyboard ANSI \ and |
    HASHTILDE_ISO = 0x32    # Keyboard ISO # and ~
    SEMICOLON = 0x33    # Keyboard ; and :
    APOSTROPHE = 0x34    # Keyboard ' and "
    GRAVE = 0x35    # Keyboard ` and ~
    COMMA = 0x36    # Keyboard , and <
    DOT = 0x37    # Keyboard . and >
    SLASH = 0x38    # Keyboard / and ?
    CAPSLOCK = 0x39    # Keyboard Caps Lock

    F1 = 0x3a    # Keyboard F1
    F2 = 0x3b    # Keyboard F2
    F3 = 0x3c    # Keyboard F3
    F4 = 0x3d    # Keyboard F4
    F5 = 0x3e    # Keyboard F5
    F6 = 0x3f    # Keyboard F6
    F7 = 0x40    # Keyboard F7
    F8 = 0x41    # Keyboard F8
    F9 = 0x42    # Keyboard F9
    F10 = 0x43    # Keyboard F10
    F11 = 0x44    # Keyboard F11
    F12 = 0x45    # Keyboard F12

    PRINT = 0x46    # Keyboard Print Screen
    SCROLLLOCK = 0x47    # Keyboard Scroll Lock
    PAUSE = 0x48    # Keyboard Pause
    INSERT = 0x49    # Keyboard Insert
    HOME = 0x4a    # Keyboard Home
    PAGEUP = 0x4b    # Keyboard Page Up
    DELETE = 0x4c    # Keyboard Delete Forward
    END = 0x4d    # Keyboard End
    PAGEDOWN = 0x4e    # Keyboard Page Down
    RIGHT = 0x4f    # Keyboard Right Arrow
    LEFT = 0x50    # Keyboard Left Arrow
    DOWN = 0x51    # Keyboard Down Arrow
    UP = 0x52    # Keyboard Up Arrow

    NUMLOCK = 0x53    # Keyboard Num Lock and Clear
    KPSLASH = 0x54    # Keypad /
    KPASTERISK = 0x55    # Keypad *
    KPMINUS = 0x56    # Keypad -
    KPPLUS = 0x57    # Keypad +
    KPENTER = 0x58    # Keypad ENTER
    KP1 = 0x59    # Keypad 1 and End
    KP2 = 0x5a    # Keypad 2 and Down Arrow
    KP3 = 0x5b    # Keypad 3 and PageDn
    KP4 = 0x5c    # Keypad 4 and Left Arrow
    KP5 = 0x5d    # Keypad 5
    KP6 = 0x5e    # Keypad 6 and Right Arrow
    KP7 = 0x5f    # Keypad 7 and Home
    KP8 = 0x60    # Keypad 8 and Up Arrow
    KP9 = 0x61    # Keypad 9 and Page Up
    KP0 = 0x62    # Keypad 0 and Insert
    KPDOT = 0x63    # Keypad . and Delete

    BACKSLASH_ISO = 0x64    # Keyboard ISO \ and |
    COMPOSE = 0x65    # Keyboard Application
    POWER = 0x66    # Keyboard Power
    KPEQUAL = 0x67    # Keypad =

    F13 = 0x68    # Keyboard F13
    F14 = 0x69    # Keyboard F14
    F15 = 0x6a    # Keyboard F15
    F16 = 0x6b    # Keyboard F16
    F17 = 0x6c    # Keyboard F17
    F18 = 0x6d    # Keyboard F18
    F19 = 0x6e    # Keyboard F19
    F20 = 0x6f    # Keyboard F20
    F21 = 0x70    # Keyboard F21
    F22 = 0x71    # Keyboard F22
    F23 = 0x72    # Keyboard F23
    F24 = 0x73    # Keyboard F24

    OPEN = 0x74    # Keyboard Execute
    HELP = 0x75    # Keyboard Help
    PROPS = 0x76    # Keyboard Menu
    FRONT = 0x77    # Keyboard Select
    STOP = 0x78    # Keyboard Stop
    AGAIN = 0x79    # Keyboard Again
    UNDO = 0x7a    # Keyboard Undo
    CUT = 0x7b    # Keyboard Cut
    COPY = 0x7c    # Keyboard Copy
    PASTE = 0x7d    # Keyboard Paste
    FIND = 0x7e    # Keyboard Find
    MUTE = 0x7f    # Keyboard Mute
    VOLUMEUP = 0x80    # Keyboard Volume Up
    VOLUMEDOWN = 0x81    # Keyboard Volume Down
    KPCOMMA = 0x85    # Keypad Comma
    RO = 0x87    # Keyboard International1
    KATAKANAHIRAGANA = 0x88    # Keyboard International2
    YEN = 0x89    # Keyboard International3
    HENKAN = 0x8a    # Keyboard International4
    MUHENKAN = 0x8b    # Keyboard International5
    KPJPCOMMA = 0x8c    # Keyboard International6
    HANGEUL = 0x90    # Keyboard LANG1
    HANJA = 0x91    # Keyboard LANG2
    KATAKANA = 0x92    # Keyboard LANG3
    HIRAGANA = 0x93    # Keyboard LANG4
    ZENKAKUHANKAKU = 0x94    # Keyboard LANG5
    KPLEFTPAREN = 0xb6    # Keypad (
    KPRIGHTPAREN = 0xb7    # Keypad )

    LEFTCTRL = 0xe0    # Keyboard Left Control
    LEFTSHIFT = 0xe1    # Keyboard Left Shift
    LEFTALT = 0xe2    # Keyboard Left Alt
    LEFTMETA = 0xe3    # Keyboard Left GUI
    RIGHTCTRL = 0xe4    # Keyboard Right Control
    RIGHTSHIFT = 0xe5    # Keyboard Right Shift
    RIGHTALT = 0xe6    # Keyboard Right Alt
    RIGHTMETA = 0xe7    # Keyboard Right GUI

    MEDIA_PLAYPAUSE = 0xe8
    MEDIA_STOPCD = 0xe9
    MEDIA_PREVIOUSSONG = 0xea
    MEDIA_NEXTSONG = 0xeb
    MEDIA_EJECTCD = 0xec
    MEDIA_VOLUMEUP = 0xed
    MEDIA_VOLUMEDOWN = 0xee
    MEDIA_MUTE = 0xef
    MEDIA_WWW = 0xf0
    MEDIA_BACK = 0xf1
    MEDIA_FORWARD = 0xf2
    MEDIA_STOP = 0xf3
    MEDIA_FIND = 0xf4
    MEDIA_SCROLLUP = 0xf5
    MEDIA_SCROLLDOWN = 0xf6
    MEDIA_EDIT = 0xf7
    MEDIA_SLEEP = 0xf8
    MEDIA_COFFEE = 0xf9
    MEDIA_REFRESH = 0xfa
    MEDIA_CALC = 0xfb

@dataclass(frozen=True)
class KeyPosition:
    x: float
    y: float
    width: float = 1.0
    height: float = 1.0
    special_shape: bool = False


# The coordinates use key units.  Every declaration begins with its USB HID
# keyboard usage (scan) code.  Empty columns separate the keyboard clusters.
key_positions_ansi: dict[ScanCode, KeyPosition] = {
    ScanCode.ESC: KeyPosition(0, 0),
    ScanCode.F1: KeyPosition(1.5, 0),
    ScanCode.F2: KeyPosition(2.5, 0),
    ScanCode.F3: KeyPosition(3.5, 0),
    ScanCode.F4: KeyPosition(4.5, 0),
    ScanCode.F5: KeyPosition(6, 0),
    ScanCode.F6: KeyPosition(7, 0),
    ScanCode.F7: KeyPosition(8, 0),
    ScanCode.F8: KeyPosition(9, 0),
    ScanCode.F9: KeyPosition(10.5, 0),
    ScanCode.F10: KeyPosition(11.5, 0),
    ScanCode.F11: KeyPosition(12.5, 0),
    ScanCode.F12: KeyPosition(13.5, 0),
    ScanCode.PRINT: KeyPosition(15.25, 0),
    ScanCode.SCROLLLOCK: KeyPosition(16.25, 0),
    ScanCode.PAUSE: KeyPosition(17.25, 0),
    ScanCode.GRAVE: KeyPosition(0, 1.25),
    ScanCode.ONE: KeyPosition(1, 1.25),
    ScanCode.TWO: KeyPosition(2, 1.25),
    ScanCode.THREE: KeyPosition(3, 1.25),
    ScanCode.FOUR: KeyPosition(4, 1.25),
    ScanCode.FIVE: KeyPosition(5, 1.25),
    ScanCode.SIX: KeyPosition(6, 1.25),
    ScanCode.SEVEN: KeyPosition(7, 1.25),
    ScanCode.EIGHT: KeyPosition(8, 1.25),
    ScanCode.NINE: KeyPosition(9, 1.25),
    ScanCode.ZERO: KeyPosition(10, 1.25),
    ScanCode.MINUS: KeyPosition(11, 1.25),
    ScanCode.EQUAL: KeyPosition(12, 1.25),
    ScanCode.BACKSPACE: KeyPosition(13, 1.25, width=2),
    ScanCode.INSERT: KeyPosition(15.25, 1.25),
    ScanCode.HOME: KeyPosition(16.25, 1.25),
    ScanCode.PAGEUP: KeyPosition(17.25, 1.25),
    ScanCode.NUMLOCK: KeyPosition(18.5, 1.25),
    ScanCode.KPSLASH: KeyPosition(19.5, 1.25),
    ScanCode.KPASTERISK: KeyPosition(20.5, 1.25),
    ScanCode.KPMINUS: KeyPosition(21.5, 1.25),
    ScanCode.TAB: KeyPosition(0, 2.25, width=1.5),
    ScanCode.Q: KeyPosition(1.5, 2.25),
    ScanCode.W: KeyPosition(2.5, 2.25),
    ScanCode.E: KeyPosition(3.5, 2.25),
    ScanCode.R: KeyPosition(4.5, 2.25),
    ScanCode.T: KeyPosition(5.5, 2.25),
    ScanCode.Y: KeyPosition(6.5, 2.25),
    ScanCode.U: KeyPosition(7.5, 2.25),
    ScanCode.I: KeyPosition(8.5, 2.25),
    ScanCode.O: KeyPosition(9.5, 2.25),
    ScanCode.P: KeyPosition(10.5, 2.25),
    ScanCode.LEFTBRACE: KeyPosition(11.5, 2.25),
    ScanCode.RIGHTBRACE: KeyPosition(12.5, 2.25),
    ScanCode.BACKSLASH_ANSI: KeyPosition(13.5, 2.25, width=1.5),
    ScanCode.DELETE: KeyPosition(15.25, 2.25),
    ScanCode.END: KeyPosition(16.25, 2.25),
    ScanCode.PAGEDOWN: KeyPosition(17.25, 2.25),
    ScanCode.KP7: KeyPosition(18.5, 2.25),
    ScanCode.KP8: KeyPosition(19.5, 2.25),
    ScanCode.KP9: KeyPosition(20.5, 2.25),
    ScanCode.KPPLUS: KeyPosition(21.5, 2.25, height=2),
    ScanCode.CAPSLOCK: KeyPosition(0, 3.25, width=1.8),
    ScanCode.A: KeyPosition(1.8, 3.25),
    ScanCode.S: KeyPosition(2.8, 3.25),
    ScanCode.D: KeyPosition(3.8, 3.25),
    ScanCode.F: KeyPosition(4.8, 3.25),
    ScanCode.G: KeyPosition(5.8, 3.25),
    ScanCode.H: KeyPosition(6.8, 3.25),
    ScanCode.J: KeyPosition(7.8, 3.25),
    ScanCode.K: KeyPosition(8.8, 3.25),
    ScanCode.L: KeyPosition(9.8, 3.25),
    ScanCode.SEMICOLON: KeyPosition(10.8, 3.25),
    ScanCode.APOSTROPHE: KeyPosition(11.8, 3.25),
    ScanCode.ENTER: KeyPosition(12.8, 3.25, width=2.2),
    ScanCode.KP4: KeyPosition(18.5, 3.25),
    ScanCode.KP5: KeyPosition(19.5, 3.25),
    ScanCode.KP6: KeyPosition(20.5, 3.25),
    ScanCode.LEFTSHIFT: KeyPosition(0, 4.25, width=2.3),
    ScanCode.Z: KeyPosition(2.3, 4.25),
    ScanCode.X: KeyPosition(3.3, 4.25),
    ScanCode.C: KeyPosition(4.3, 4.25),
    ScanCode.V: KeyPosition(5.3, 4.25),
    ScanCode.B: KeyPosition(6.3, 4.25),
    ScanCode.N: KeyPosition(7.3, 4.25),
    ScanCode.M: KeyPosition(8.3, 4.25),
    ScanCode.COMMA: KeyPosition(9.3, 4.25),
    ScanCode.DOT: KeyPosition(10.3, 4.25),
    ScanCode.SLASH: KeyPosition(11.3, 4.25),
    ScanCode.RIGHTSHIFT: KeyPosition(12.3, 4.25, width=2.7),
    ScanCode.UP: KeyPosition(16.25, 4.25),
    ScanCode.KP1: KeyPosition(18.5, 4.25),
    ScanCode.KP2: KeyPosition(19.5, 4.25),
    ScanCode.KP3: KeyPosition(20.5, 4.25),
    ScanCode.KPENTER: KeyPosition(21.5, 4.25, height=2),
    ScanCode.LEFTCTRL: KeyPosition(0, 5.25, width=1.35),
    ScanCode.LEFTMETA: KeyPosition(1.35, 5.25, width=1.25),
    ScanCode.LEFTALT: KeyPosition(2.6, 5.25, width=1.25),
    ScanCode.SPACE: KeyPosition(3.85, 5.25, width=6.3),
    ScanCode.RIGHTALT: KeyPosition(10.15, 5.25, width=1.25),
    ScanCode.RIGHTMETA: KeyPosition(11.4, 5.25, width=1.1),
    ScanCode.PROPS: KeyPosition(12.5, 5.25, width=1.2),
    ScanCode.RIGHTCTRL: KeyPosition(13.7, 5.25, width=1.3),
    ScanCode.LEFT: KeyPosition(15.25, 5.25),
    ScanCode.DOWN: KeyPosition(16.25, 5.25),
    ScanCode.RIGHT: KeyPosition(17.25, 5.25),
    ScanCode.KP0: KeyPosition(18.5, 5.25, width=2),
    ScanCode.KPDOT: KeyPosition(20.5, 5.25),
}

key_positions_iso = key_positions_ansi.copy()
key_positions_iso.pop(ScanCode.BACKSLASH_ANSI)
key_positions_iso[ScanCode.LEFTSHIFT] = KeyPosition(0, 4.25, width=1.3)
key_positions_iso[ScanCode.BACKSLASH_ISO] = KeyPosition(1.3, 4.25)
key_positions_iso[ScanCode.HASHTILDE_ISO] = KeyPosition(12.8, 3.25)
key_positions_iso[ScanCode.ENTER] = KeyPosition(13.5, 2.25, width=1.5, height=2, special_shape=True)

class PhysicalLayout(Enum):
    """Physical keyboard layouts."""
    ANSI = 1
    ISO = 2

physical_layouts = {
    PhysicalLayout.ANSI: key_positions_ansi,
    PhysicalLayout.ISO: key_positions_iso,
}

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

@dataclass(frozen=True)
class KeyboardLayout:
    """A keyboard layout, which maps physical keys to characters."""
    name: str
    physical_layout: PhysicalLayout
    modifiers: dict[ScanCode, tuple[Modifier, bool]]  # The bool determines whether the modifier is sticky (e.g., Num Lock) or not.
    keys: dict[ScanCode, LayoutKey]

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

layout_en_us = KeyboardLayout(
    name="en-US",
    physical_layout=PhysicalLayout.ANSI,
    modifiers={
        ScanCode.LEFTSHIFT: (Modifier.SHIFT, False),
        ScanCode.RIGHTSHIFT: (Modifier.SHIFT, False),
        ScanCode.RIGHTALT: (Modifier.ALT, False),
        ScanCode.NUMLOCK: (Modifier.NUMLK, True),
    },
    keys={
        **general_keys,

        ScanCode.PRINT: LayoutKey("Print", is_character=False),
        ScanCode.SCROLLLOCK: LayoutKey("Scroll\nLock", is_character=False),
        ScanCode.PAUSE: LayoutKey("Pause", is_character=False),
        ScanCode.GRAVE: LayoutKey("`", {Modifier.SHIFT: "~"}),
        ScanCode.ONE: LayoutKey("1", {Modifier.SHIFT: "!"}),
        ScanCode.TWO: LayoutKey("2", {Modifier.SHIFT: "@"}),
        ScanCode.THREE: LayoutKey("3", {Modifier.SHIFT: "#"}),
        ScanCode.FOUR: LayoutKey("4", {Modifier.SHIFT: "$"}),
        ScanCode.FIVE: LayoutKey("5", {Modifier.SHIFT: "%"}),
        ScanCode.SIX: LayoutKey("6", {Modifier.SHIFT: "^"}),
        ScanCode.SEVEN: LayoutKey("7", {Modifier.SHIFT: "&"}),
        ScanCode.EIGHT: LayoutKey("8", {Modifier.SHIFT: "*"}),
        ScanCode.NINE: LayoutKey("9", {Modifier.SHIFT: "("}),
        ScanCode.ZERO: LayoutKey("0", {Modifier.SHIFT: ")"}),
        ScanCode.MINUS: LayoutKey("-", {Modifier.SHIFT: "_"}),
        ScanCode.EQUAL: LayoutKey("=", {Modifier.SHIFT: "+"}),
        ScanCode.BACKSPACE: LayoutKey("⌫", is_character=False),
        ScanCode.TAB: LayoutKey("⇤\n⇥", is_character=False, representation="⇥"),
        ScanCode.Q: LayoutKey("q", {Modifier.SHIFT: "Q"}),
        ScanCode.W: LayoutKey("w", {Modifier.SHIFT: "W"}),
        ScanCode.E: LayoutKey("e", {Modifier.SHIFT: "E"}),
        ScanCode.R: LayoutKey("r", {Modifier.SHIFT: "R"}),
        ScanCode.T: LayoutKey("t", {Modifier.SHIFT: "T"}),
        ScanCode.Y: LayoutKey("y", {Modifier.SHIFT: "Y"}),
        ScanCode.U: LayoutKey("u", {Modifier.SHIFT: "U"}),
        ScanCode.I: LayoutKey("i", {Modifier.SHIFT: "I"}),
        ScanCode.O: LayoutKey("o", {Modifier.SHIFT: "O"}),
        ScanCode.P: LayoutKey("p", {Modifier.SHIFT: "P"}),
        ScanCode.LEFTBRACE: LayoutKey("[", {Modifier.SHIFT: "{"}),
        ScanCode.RIGHTBRACE: LayoutKey("]", {Modifier.SHIFT: "}"}),
        ScanCode.BACKSLASH_ANSI: LayoutKey("\\", {Modifier.SHIFT: "|"}),
        ScanCode.CAPSLOCK: LayoutKey("⇪", is_character=False),
        ScanCode.A: LayoutKey("a", {Modifier.SHIFT: "A"}),
        ScanCode.S: LayoutKey("s", {Modifier.SHIFT: "S"}),
        ScanCode.D: LayoutKey("d", {Modifier.SHIFT: "D"}),
        ScanCode.F: LayoutKey("f", {Modifier.SHIFT: "F"}),
        ScanCode.G: LayoutKey("g", {Modifier.SHIFT: "G"}),
        ScanCode.H: LayoutKey("h", {Modifier.SHIFT: "H"}),
        ScanCode.J: LayoutKey("j", {Modifier.SHIFT: "J"}),
        ScanCode.K: LayoutKey("k", {Modifier.SHIFT: "K"}),
        ScanCode.L: LayoutKey("l", {Modifier.SHIFT: "L"}),
        ScanCode.SEMICOLON: LayoutKey(";", {Modifier.SHIFT: ":"}),
        ScanCode.APOSTROPHE: LayoutKey("'", {Modifier.SHIFT: "\""}),
        ScanCode.ENTER: LayoutKey("↵"),
        ScanCode.LEFTSHIFT: LayoutKey("⇧", is_character=False),
        ScanCode.Z: LayoutKey("z", {Modifier.SHIFT: "Z"}),
        ScanCode.X: LayoutKey("x", {Modifier.SHIFT: "X"}),
        ScanCode.C: LayoutKey("c", {Modifier.SHIFT: "C"}),
        ScanCode.V: LayoutKey("v", {Modifier.SHIFT: "V"}),
        ScanCode.B: LayoutKey("b", {Modifier.SHIFT: "B"}),
        ScanCode.N: LayoutKey("n", {Modifier.SHIFT: "N"}),
        ScanCode.M: LayoutKey("m", {Modifier.SHIFT: "M"}),
        ScanCode.COMMA: LayoutKey(",", {Modifier.SHIFT: "<"}),
        ScanCode.DOT: LayoutKey(".", {Modifier.SHIFT: ">"}),
        ScanCode.SLASH: LayoutKey("/", {Modifier.SHIFT: "?"}),
        ScanCode.RIGHTSHIFT: LayoutKey("⇧", is_character=False, representation="RShift"),
        ScanCode.LEFTCTRL: LayoutKey("Ctrl", is_character=False, representation="LCtrl"),
        ScanCode.LEFTMETA: LayoutKey("Win", is_character=False, representation="LWin"),
        ScanCode.LEFTALT: LayoutKey("Alt", is_character=False, representation="LAlt"),
        ScanCode.SPACE: LayoutKey("␣", is_character=False),
        ScanCode.RIGHTALT: LayoutKey("Alt", is_character=False, representation="RAlt"),
        ScanCode.RIGHTMETA: LayoutKey("Win", is_character=False, representation="RWin"),
        ScanCode.PROPS: LayoutKey("Menu", is_character=False),
        ScanCode.RIGHTCTRL: LayoutKey("Ctrl", is_character=False, representation="RCtrl"),

        ScanCode.INSERT: LayoutKey("Ins", is_character=False),
        ScanCode.HOME: LayoutKey("Home", is_character=False),
        ScanCode.PAGEUP: LayoutKey("PgUp", is_character=False),
        ScanCode.DELETE: LayoutKey("Del", is_character=False),
        ScanCode.END: LayoutKey("End", is_character=False),
        ScanCode.PAGEDOWN: LayoutKey("PgDn", is_character=False),

        ScanCode.NUMLOCK: LayoutKey("Num\nLock", is_character=False, representation="NumLock"),
        ScanCode.KPSLASH: LayoutKey("/", representation="⊘"),
        ScanCode.KPASTERISK: LayoutKey("*", representation="⊛"),
        ScanCode.KPMINUS: LayoutKey("-", representation="⊖"),
        ScanCode.KP7: LayoutKey("7", {Modifier.NUMLK: "Home"}, representation="⑦"),
        ScanCode.KP8: LayoutKey("8", {Modifier.NUMLK: "↑"}, representation="⑧"),
        ScanCode.KP9: LayoutKey("9", {Modifier.NUMLK: "PgUp"}, representation="⑨"),
        ScanCode.KPPLUS: LayoutKey("+", representation="⊕"),
        ScanCode.KP4: LayoutKey("4", {Modifier.NUMLK: "←"}, representation="④"),
        ScanCode.KP5: LayoutKey("5", representation="⑤"),
        ScanCode.KP6: LayoutKey("6", {Modifier.NUMLK: "→"}, representation="⑥"),
        ScanCode.KP1: LayoutKey("1", {Modifier.NUMLK: "End"}, representation="①"),
        ScanCode.KP2: LayoutKey("2", {Modifier.NUMLK: "↓"}, representation="②"),
        ScanCode.KP3: LayoutKey("3", {Modifier.NUMLK: "PgDn"}, representation="③"),
        ScanCode.KPENTER: LayoutKey("Enter", representation="⏎"),
        ScanCode.KP0: LayoutKey("0", {Modifier.NUMLK: "Ins"}, representation="⓪"),
        ScanCode.KPDOT: LayoutKey(".", {Modifier.NUMLK: "Del"}, representation="⨀"),
    }
)

layout_de_de = KeyboardLayout(
    name="de-DE",
    physical_layout=PhysicalLayout.ISO,
    modifiers={
        ScanCode.LEFTSHIFT: (Modifier.SHIFT, False),
        ScanCode.RIGHTSHIFT: (Modifier.SHIFT, False),
        ScanCode.RIGHTALT: (Modifier.ALTGR, False),
        ScanCode.NUMLOCK: (Modifier.NUMLK, True),
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

@dataclass
class KeyLabels:
    """The labels to display on a physical key."""
    primary: str | None
    top_left: str | None = None
    top_right: str | None = None
    bottom_left: str | None = None
    bottom_right: str | None = None

class KeyboardWidget(QWidget):
    """Paints a responsive keyboard and highlights the last clicked key."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(980, 460)
        self.setMouseTracking(True)
        self._hovered: KeyPosition | None = None
        self._selected: KeyPosition | None = None
        self._key_rects: list[tuple[KeyPosition, QRectF]] = []
        self._layout = layout_en_us

    def _key_at(self, point: QPointF) -> KeyPosition | None:
        for key, rect in self._key_rects:
            if rect.contains(point):
                return key
        return None

    def set_layout(self, layout: KeyboardLayout) -> None:
        self._layout = layout
        self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # type: ignore[override]
        key = self._key_at(event.position())
        if key != self._hovered:
            self._hovered = key
            self.setCursor(Qt.CursorShape.PointingHandCursor if key else Qt.CursorShape.ArrowCursor)
            self.update()

    def leaveEvent(self, event: QEvent) -> None:  # type: ignore[override]
        self._hovered = None
        self.update()

    def mousePressEvent(self, event: QMouseEvent) -> None:  # type: ignore[override]
        if event.button() == Qt.MouseButton.LeftButton:
            self._selected = self._key_at(event.position())
            self.update()

    def paintEvent(self, event: QPaintEvent) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#0d1017"))

        area = QRectF(self.rect()).adjusted(46, 46, -46, -46)

        key_positions = physical_layouts[self._layout.physical_layout]

        bottom_right = key_positions[ScanCode.KPENTER]
        total_columns = bottom_right.x + bottom_right.width
        total_rows = bottom_right.y + bottom_right.height
        gap = 8.0
        key_width = (area.width() - gap * (total_columns - 1)) / total_columns
        key_height = min((area.height() - gap * (total_rows - 1)) / total_rows, key_width * 0.92)
        board_height = key_height * total_rows + gap * (total_rows - 1)
        top = area.center().y() - board_height / 2
        self._key_rects.clear()

        chassis = QRectF(area.left() - 16, top - 16, area.width() + 32, board_height + 32)
        painter.setPen(QPen(QColor("#2a3140"), 1))
        painter.setBrush(QColor("#151a24"))
        painter.drawRoundedRect(chassis, 18, 18)

        for key, value in key_positions.items():
            x = area.left() + value.x * (key_width + gap)
            y = top + value.y * (key_height + gap)
            width = value.width * key_width + (value.width - 1) * gap
            height = value.height * key_height + (value.height - 1) * gap
            rect = QRectF(x, y, width, height)
            self._key_rects.append((value, rect))
            label = self._layout.keys.get(key)
            if label:
                label = KeyLabels(
                    primary=label.primary,
                    top_left=label.additional.get(Modifier.SHIFT) if label.additional else None,
                    top_right=label.additional.get(Modifier.CTRL) if label.additional else None,
                    bottom_left=label.additional.get(Modifier.NUMLK) if label.additional else None,
                    bottom_right=label.additional.get(Modifier.ALTGR) if label.additional else None,
                )
            else:
                label = KeyLabels(
                    primary="",
                    top_left=None,
                    top_right=None,
                    bottom_left=None,
                    bottom_right=None,
                )

            self._draw_Key(painter, rect, value, label, value.special_shape)

        painter.end()

    def _draw_Key(self, painter: QPainter, rect: QRectF, key: KeyPosition, labels: KeyLabels, special_shape: bool) -> None:
        is_active = key == self._selected
        is_hovered = key == self._hovered
        if is_active:
            fill, border, label_color = QColor("#5b8cff"), QColor("#9bb7ff"), QColor("#ffffff")
        elif is_hovered:
            fill, border, label_color = QColor("#303b51"), QColor("#627393"), QColor("#f3f6ff")
        else:
            fill, border, label_color = QColor("#202735"), QColor("#394456"), QColor("#d9dfeb")

        painter.setPen(QPen(border, 1))
        painter.setBrush(fill)
        r = 8
        if special_shape:
            wl = rect.width() / 1.5 * 0.3
            bl = rect.left() + wl
            bh = rect.top() + rect.height() / 2 - 4
            path = QPainterPath()
            path.moveTo(rect.left() + r, rect.top())
            path.lineTo(rect.right() - r, rect.top())
            path.quadTo(rect.right(), rect.top(), rect.right(), rect.top() + r)
            path.lineTo(rect.right(), rect.bottom() - r)
            path.quadTo(rect.right(), rect.bottom(), rect.right() - r, rect.bottom())
            path.lineTo(bl + r, rect.bottom())
            path.quadTo(bl, rect.bottom(), bl, rect.bottom() - r)
            path.lineTo(bl, bh + r)
            path.quadTo(bl, bh, bl - r, bh)
            path.lineTo(rect.left() + r, bh)
            path.quadTo(rect.left(), bh, rect.left(), bh - r)
            path.lineTo(rect.left(), rect.top() + r)
            path.quadTo(rect.left(), rect.top(), rect.left() + r, rect.top())
            painter.drawPath(path)
            textrect = QRectF(bl, rect.top(), rect.width() - wl, rect.height())
        else:
            path = QPainterPath()
            path.addRoundedRect(rect, r, r)
            painter.drawPath(path)
            textrect = rect


        label_rects = [
            (textrect, labels.primary),
            (QRectF(textrect.left(), textrect.top(), textrect.width() /2, textrect.height() / 2), labels.top_left),
            (QRectF(textrect.right() - textrect.width() / 2, textrect.top(), textrect.width() / 2, textrect.height() / 2), labels.top_right),
            (QRectF(textrect.left(), textrect.bottom() - textrect.height() / 2, textrect.width() / 2, textrect.height() / 2), labels.bottom_left),
            (QRectF(textrect.right() - textrect.width() / 2, textrect.bottom() - textrect.height() / 2, textrect.width() / 2, textrect.height() / 2), labels.bottom_right),
        ]
        for rect, label in label_rects:
            if label:
                font_size = max(8, min(15, int(min(rect.height(), rect.width()) * (0.18 if label and len(label) > 1 else 0.32))))
                painter.setFont(QFont("Inter", font_size, QFont.Weight.DemiBold))
                painter.setPen(label_color)
                painter.drawText(rect.adjusted(6, 4, -6, -4), Qt.AlignmentFlag.AlignCenter, label)


class KeyboardWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Keyboard Layout")
        self._keyboard_widget = KeyboardWidget()
        self.setCentralWidget(self._keyboard_widget)

        top_widget = QDockWidget()
        top_container = QWidget()
        top_layout = QHBoxLayout()
        top_container.setLayout(top_layout)
        top_widget.setWidget(top_container)
        self.layout_selector = QComboBox()
        self.layout_selector.addItem("en-US", layout_en_us)
        self.layout_selector.addItem("de-DE", layout_de_de)
        top_layout.addStretch()
        top_layout.addWidget(self.layout_selector)
        top_layout.addStretch()
        self.layout_selector.currentIndexChanged.connect(self.on_layout_changed)
        self.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea, top_widget)

        self.resize(1500, 640)

    def on_layout_changed(self, index: int) -> None:
        layout = self.layout_selector.itemData(index)
        self._keyboard_widget.set_layout(layout)


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = KeyboardWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
