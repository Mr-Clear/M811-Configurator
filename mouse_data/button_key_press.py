from ui.keyboard.usb_hid import ModifierCode, ScanCode
from mouse_data import MouseData
from mouse_data.button import Button


class ButtonKeyPress(Button):
    ''' Button that is mapped to a keyboard key including modifiers. '''

    def __init__(self, mouse: MouseData, offset: int):
        super().__init__(mouse, offset)

    @classmethod
    def type_name(cls) -> str:
        return "Key Press"

    @classmethod
    def is_data_valid(cls, mouse: MouseData, offset: int) -> bool:
        data = list(mouse.data[offset:offset + Button.DATA_LENGTH])
        if data[0] != 0x90 and data[0] != 0x8f:
            return False
        if data[2] not in [scan_code.value for scan_code in ScanCode]:
            return False
        return True

    def set_default(self) -> None:
        data = bytearray(self.raw_data)
        data[0] = 0x90
        self.key = ScanCode.A
        self.modifiers = ModifierCode(0)
        self.raw_data = bytes([
            0x90,
            0x00, # no modifiers
            ScanCode.A.value,
            0x00, # reserved
        ])

    @property
    def key(self) -> ScanCode:
        ''' The scan code of the key press. '''
        return ScanCode(self.raw_data[2])

    @key.setter
    def key(self, scan_code: ScanCode) -> None:
        ''' Set the scan code of the key press. '''
        data = bytearray(self.raw_data)
        data[2] = scan_code.value
        self.raw_data = data

    @property
    def modifiers(self) -> ModifierCode:
        ''' The modifiers of the key press. '''
        modifiers = ModifierCode(0)
        for modifier in ModifierCode:
            if self.raw_data[1] & modifier.value:
                modifiers |= modifier
        return modifiers

    @modifiers.setter
    def modifiers(self, modifiers: ModifierCode) -> None:
        ''' Set the modifiers of the key press. '''
        data = bytearray(self.raw_data)
        i = 0
        for modifier in modifiers:
            i |= modifier.value
        data[1] = i
        self.raw_data = data

    def _modifiers_str(self) -> str:
        modifiers_str = ""
        for modifier in ModifierCode:
            if self.raw_data[1] & modifier.value:
                modifiers_str += f'{modifier.name}+'
        return modifiers_str[:-1] if modifiers_str else ""

    def __str__(self) -> str:
        modifiers_str = self._modifiers_str()
        scan_code_str = f"{self.key} ({self.raw_data[2]:#02x})"
        if modifiers_str:
            return f"{modifiers_str}+{scan_code_str}"
        else:
            return f"{scan_code_str}"
