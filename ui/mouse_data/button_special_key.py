from enum import Enum

from ui.mouse_data import MouseData
from ui.mouse_data.button import Button


class ButtonSpecialKey(Button):
    ''' Button that is mapped to a special function. '''
    class Type(Enum):
        MEDIA_NEXT = [0x8e, 0x01, 0xb5, 0x00]
        MEDIA_PREVIOUS = [0x8e, 0x01, 0xb6, 0x00]
        MEDIA_STOP = [0x8e, 0x01, 0xb7, 0x00]
        MEDIA_PLAY_PAUSE = [0x8e, 0x01, 0xcd, 0x00]
        MEDIA_VOLUME_UP = [0x8e, 0x01, 0xe9, 0x00]
        MEDIA_VOL_DOWN = [0x8e, 0x01, 0xea, 0x00]
        MEDIA_MUTE = [0x8e, 0x01, 0xe2, 0x00]

        BROWSER_HOME = [0x8e, 0x01, 0xFF, 0x1F]
        BROWSER_BACK = [0x8e, 0x01, 0xFF, 0x20]
        BROWSER_FORWARD = [0x8e, 0x01, 0xFF, 0x21]
        BROWSER_STOP = [0x8e, 0x01, 0xFF, 0x22]
        BROWSER_REFRESH = [0x8e, 0x01, 0xFF, 0x23]
        BROWSER_SEARCH = [0x8e, 0x01, 0xFF, 0x24]
        BROWSER_FAVORITES = [0x8e, 0x01, 0xFF, 0x25]
        MAIL = [0x8e, 0x01, 0xFF, 0x26]

        @staticmethod
        def names():
            T = ButtonSpecialKey.Type
            return {
                T.MEDIA_NEXT: "Next",
                T.MEDIA_PREVIOUS: "Previous",
                T.MEDIA_STOP: "Stop",
                T.MEDIA_PLAY_PAUSE: "Play/Pause",
                T.MEDIA_VOLUME_UP: "Volume Up",
                T.MEDIA_VOL_DOWN: "Volume Down",
                T.MEDIA_MUTE: "Mute",

                T.BROWSER_HOME: "Browser Home",
                T.BROWSER_BACK: "Browser Back",
                T.BROWSER_FORWARD: "Browser Forward",
                T.BROWSER_STOP: "Browser Stop",
                T.BROWSER_REFRESH: "Browser Refresh",
                T.BROWSER_SEARCH: "Browser Search",
                T.BROWSER_FAVORITES: "Browser Favorites",
                T.MAIL: "Mail",
            }

        @property
        def name(self) -> str:
            return self.names()[self]

    def __init__(self, mouse: MouseData, offset: int):
        super().__init__(mouse, offset)

    @classmethod
    def type_name(cls) -> str:
        return "Special Key"

    @classmethod
    def is_data_valid(cls, mouse: MouseData, offset: int) -> bool:
        data = list(mouse.data[offset:offset + Button.DATA_LENGTH])
        return data in [function.value for function in ButtonSpecialKey.Type]

    def set_default(self) -> None:
        self.raw_data = bytes(ButtonSpecialKey.Type.MEDIA_PLAY_PAUSE.value)

    @property
    def special_key_type(self) -> Type:
        return ButtonSpecialKey.Type(list(self.raw_data))
    @special_key_type.setter
    def special_key_type(self, value: Type) -> None:
        self.raw_data = bytes(value.value)

    def __str__(self) -> str:
        return f"{self.special_key_type.name}"
