from ui.keyboard import Modifier, ScanCode
from ui.mouse_data import MouseData
from ui.mouse_data.button import Button


class ButtonKeyPress(Button):
    ''' Button that is mapped to a keyboard key including modifiers. '''

    def __init__(self, mouse: MouseData, offset: int):
        data = list(mouse.data[offset:offset + 4])
        if data[0] != 0x90 and data[0] != 0x8f:
            raise ValueError(f"Invalid KeyPress data: {data}")
        self._modifiers = data[1]
        self._scan_code = data[2]
        if self._scan_code not in [scan_code.code for scan_code in ScanCode]:
            raise ValueError(f"Invalid scan code: {self._scan_code:#02x}")
        super().__init__(mouse, offset)

    @classmethod
    def type_name(cls) -> str:
        return "Key Press"

    @property
    def key(self) -> ScanCode:
        ''' The scan code of the key press. '''
        return ScanCode.from_code(self._scan_code)
    @key.setter
    def key(self, scan_code: ScanCode) -> None:
        ''' Set the scan code of the key press. '''
        self._scan_code = scan_code.code

    @property
    def modifiers(self) -> set[Modifier]:
        ''' The modifiers of the key press. '''
        modifiers: set[Modifier] = set()
        for modifier in Modifier:
            if self._modifiers & modifier.value:
                modifiers.add(modifier)
        return modifiers

    @modifiers.setter
    def modifiers(self, modifiers: set[Modifier]) -> None:
        ''' Set the modifiers of the key press. '''
        i = 0
        for modifier in modifiers:
            i |= modifier.value
        self._modifiers = i

    def to_raw(self) -> list[int]:
        return [0x90 if self._modifiers == 0 else 0x8f, self._modifiers, self._scan_code, 0x00]

    def _modifiers_str(self) -> str:
        modifiers_str = ""
        for modifier in Modifier:
            if self._modifiers & modifier.value:
                modifiers_str += modifier.name + "+"
        return modifiers_str[:-1] if modifiers_str else ""

    def __str__(self) -> str:
        modifiers_str = self._modifiers_str()
        scan_code_str = f"{ScanCode.from_code(self._scan_code).key_name()} ({self._scan_code:#02x})"
        if modifiers_str:
            return f"{modifiers_str}+{scan_code_str}"
        else:
            return f"{scan_code_str}"
