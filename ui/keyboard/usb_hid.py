from enum import Enum, Flag


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

    @classmethod
    def modifiers(cls) -> set[ScanCode]:
        return {
            cls.LEFTCTRL,
            cls.LEFTSHIFT,
            cls.LEFTALT,
            cls.LEFTMETA,
            cls.RIGHTCTRL,
            cls.RIGHTSHIFT,
            cls.RIGHTALT,
            cls.RIGHTMETA,
        }

    @classmethod
    def function_keys(cls) -> set[ScanCode]:
        return {
            cls.F1,
            cls.F2,
            cls.F3,
            cls.F4,
            cls.F5,
            cls.F6,
            cls.F7,
            cls.F8,
            cls.F9,
            cls.F10,
            cls.F11,
            cls.F12,
        }

    @classmethod
    def cursor_keys(cls) -> set[ScanCode]:
        return {
            cls.UP,
            cls.DOWN,
            cls.LEFT,
            cls.RIGHT,
        }

    @classmethod
    def position_keys(cls) -> set[ScanCode]:
        return {
            cls.INSERT,
            cls.HOME,
            cls.PAGEUP,
            cls.DELETE,
            cls.END,
            cls.PAGEDOWN,
        }

    @classmethod
    def numpad_keys(cls) -> set[ScanCode]:
        return {
            cls.KP0,
            cls.KP1,
            cls.KP2,
            cls.KP3,
            cls.KP4,
            cls.KP5,
            cls.KP6,
            cls.KP7,
            cls.KP8,
            cls.KP9,
            cls.KPDOT,
            cls.KPSLASH,
            cls.KPASTERISK,
            cls.KPMINUS,
            cls.KPPLUS,
            cls.KPENTER,
        }

    @classmethod
    def system_control_keys(cls) -> set[ScanCode]:
        return {
            cls.PRINT,
            cls.SCROLLLOCK,
            cls.PAUSE,
        }

    @classmethod
    def media_keys(cls) -> set[ScanCode]:
        return {
            cls.MEDIA_PLAYPAUSE,
            cls.MEDIA_STOPCD,
            cls.MEDIA_PREVIOUSSONG,
            cls.MEDIA_NEXTSONG,
            cls.MEDIA_EJECTCD,
            cls.MEDIA_VOLUMEUP,
            cls.MEDIA_VOLUMEDOWN,
            cls.MEDIA_MUTE,
            cls.MEDIA_WWW,
            cls.MEDIA_BACK,
            cls.MEDIA_FORWARD,
            cls.MEDIA_STOP,
            cls.MEDIA_FIND,
            cls.MEDIA_SCROLLUP,
            cls.MEDIA_SCROLLDOWN,
            cls.MEDIA_EDIT,
            cls.MEDIA_SLEEP,
            cls.MEDIA_COFFEE,
            cls.MEDIA_REFRESH,
            cls.MEDIA_CALC,
        }

    @property
    def is_modifier(self) -> bool:
        return self in self.modifiers()

    @property
    def is_function_key(self) -> bool:
        return self in self.function_keys()

    @property
    def is_cursor_key(self) -> bool:
        return self in self.cursor_keys()

    @property
    def is_position_key(self) -> bool:
        return self in self.position_keys()

    @property
    def is_numpad_key(self) -> bool:
        return self in self.numpad_keys()

    @property
    def is_system_control_key(self) -> bool:
        return self in self.system_control_keys()

    @property
    def is_media_key(self) -> bool:
        return self in self.media_keys()


class ModifierCode(Flag):
    NONE = 0x00
    LCtrl = 0x01
    LShift = 0x02
    LAlt = 0x04
    LWin = 0x08
    RCtrl = 0x10
    RShift = 0x20
    RAlt = 0x40
    RWin = 0x80

modifier_keys = {
    ScanCode.LEFTCTRL: ModifierCode.LCtrl,
    ScanCode.LEFTSHIFT: ModifierCode.LShift,
    ScanCode.LEFTALT: ModifierCode.LAlt,
    ScanCode.LEFTMETA: ModifierCode.LWin,
    ScanCode.RIGHTCTRL: ModifierCode.RCtrl,
    ScanCode.RIGHTSHIFT: ModifierCode.RShift,
    ScanCode.RIGHTALT: ModifierCode.RAlt,
    ScanCode.RIGHTMETA: ModifierCode.RWin,
}

# From hid-input.c
hid_keyboard_table: list[int | None] = [
	   0,   0,   0,   0,  30,  48,  46,  32,  18,  33,  34,  35,  23,  36,  37,  38,
	  50,  49,  24,  25,  16,  19,  31,  20,  22,  47,  17,  45,  21,  44,   2,   3,
	   4,   5,   6,   7,   8,   9,  10,  11,  28,   1,  14,  15,  57,  12,  13,  26,
	  27,  43,  43,  39,  40,  41,  51,  52,  53,  58,  59,  60,  61,  62,  63,  64,
	  65,  66,  67,  68,  87,  88,  99,  70, 119, 110, 102, 104, 111, 107, 109, 106,
	 105, 108, 103,  69,  98,  55,  74,  78,  96,  79,  80,  81,  75,  76,  77,  71,
	  72,  73,  82,  83,  86, 127, 116, 117, 183, 184, 185, 186, 187, 188, 189, 190,
	 191, 192, 193, 194, 134, 138, 130, 132, 128, 129, 131, 137, 133, 135, 136, 113,
	 115, 114,None,None,None, 121,None,  89,  93, 124,  92,  94,  95,None,None,None,
	 122, 123,  90,  91,  85,None,None,None,None,None,None,None, 111,None,None,None,
	None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,
	None,None,None,None,None,None, 179, 180,None,None,None,None,None,None,None,None,
	None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,
	None,None,None,None,None,None,None,None, 111,None,None,None,None,None,None,None,
	  29,  42,  56, 125,  97,  54, 100, 126, 164, 166, 165, 163, 161, 115, 114, 113,
	 150, 158, 159, 128, 136, 177, 178, 176, 142, 152, 173, 140,None,None,None,None
]

def native_scan_code_to_hid(native_scan_code: int) -> ScanCode | None:
    """Convert a Qt native scan code to a USB HID scan code."""
    linux_code = native_scan_code - 8
    try:
        return ScanCode(hid_keyboard_table.index(linux_code))
    except ValueError:
        return None
