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
            return {
                ButtonSpecialKey.Type.MEDIA_NEXT: "Next",
                ButtonSpecialKey.Type.MEDIA_PREVIOUS: "Previous",
                ButtonSpecialKey.Type.MEDIA_STOP: "Stop",
                ButtonSpecialKey.Type.MEDIA_PLAY_PAUSE: "Play/Pause",
                ButtonSpecialKey.Type.MEDIA_VOLUME_UP: "Volume Up",
                ButtonSpecialKey.Type.MEDIA_VOL_DOWN: "Volume Down",
                ButtonSpecialKey.Type.MEDIA_MUTE: "Mute",

                ButtonSpecialKey.Type.BROWSER_HOME: "Browser Home",
                ButtonSpecialKey.Type.BROWSER_BACK: "Browser Back",
                ButtonSpecialKey.Type.BROWSER_FORWARD: "Browser Forward",
                ButtonSpecialKey.Type.BROWSER_STOP: "Browser Stop",
                ButtonSpecialKey.Type.BROWSER_REFRESH: "Browser Refresh",
                ButtonSpecialKey.Type.BROWSER_SEARCH: "Browser Search",
                ButtonSpecialKey.Type.BROWSER_FAVORITES: "Browser Favorites",
                ButtonSpecialKey.Type.MAIL: "Mail",
            }

        @property
        def name(self) -> str:
            return self.names()[self]

    def __init__(self, mouse: MouseData, offset: int):
        data = list(mouse.data[offset:offset + 4])
        if data in [function.value for function in ButtonSpecialKey.Type]:
            self.type = ButtonSpecialKey.Type(data)
        else:
            raise ValueError(f"Invalid SpecialKey data: {data}")
        super().__init__(mouse, offset)

    @classmethod
    def type_name(cls) -> str:
        return "Special Key"

    def to_raw(self) -> list[int]:
        return self.type.value

    def __str__(self) -> str:
        return f"{self.type.name}"
