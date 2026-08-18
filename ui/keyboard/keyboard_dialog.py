from PySide6.QtCore import Signal
from PySide6.QtWidgets import (QDialog, QHBoxLayout, QLabel, QPushButton,
                               QVBoxLayout, QWidget)

from .keyboard_widget import (KeyboardWidget, KeyColors, KeyWidget,
                              ModifierCode, ScanCode)
from .layouts import KeyboardLayout


class KeyboardDialog(QDialog):
    """Dialog for displaying a keyboard layout and capturing key events."""
    key_down = Signal(ScanCode, ModifierCode)
    key_up = Signal(ScanCode)

    def __init__(self, keyboard_layout: KeyboardLayout, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._keyboard_layout = keyboard_layout
        self.setMinimumSize(400, 300)
        self.setWindowTitle(title)
        self._scan_code: ScanCode | None = None
        self._modifiers: ModifierCode = ModifierCode.NONE

        layout = QVBoxLayout(self)

        self._keyboard_widget = KeyboardWidget()
        self._keyboard_widget.keyboard_layout = self._keyboard_layout
        self._keyboard_widget.key_down.connect(self.key_down)
        self._keyboard_widget.key_down.connect(self._set_key)
        self._keyboard_widget.key_up.connect(self.key_up)
        layout.addWidget(self._keyboard_widget)

        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch(1)

        palette = self.palette()
        self._key_widget = KeyWidget(
            scan_code=None,
            modifiers=ModifierCode.NONE,
            keyboard_layout=self._keyboard_layout,
            colors=KeyColors(
                background=palette.color(palette.ColorRole.Dark),
                border=palette.color(palette.ColorRole.Light),
                text=palette.color(palette.ColorRole.WindowText),
            ),
        )
        self._key_widget.setFixedSize(48, 48)
        bottom_layout.addWidget(self._key_widget)
        bottom_layout.addSpacing(8)
        self._key_label = QLabel()
        self._key_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        bottom_layout.addWidget(self._key_label)
        bottom_layout.addStretch(1)

        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        bottom_layout.addWidget(ok_button)
        bottom_layout.addWidget(cancel_button)
        layout.addLayout(bottom_layout)

        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)

    @property
    def scan_code(self) -> ScanCode | None:
        """Return the scan code of the key currently displayed in the dialog."""
        return self._scan_code
    @property
    def modifiers(self) -> ModifierCode:
        """Return the modifiers of the key currently displayed in the dialog."""
        return self._modifiers

    def _set_key(self, scan_code: ScanCode, modifiers: ModifierCode) -> None:
        """Set the key and modifiers to be displayed in the dialog."""
        self._scan_code = scan_code
        self._modifiers = modifiers
        self._key_widget.scan_code = scan_code
        self._key_widget.modifiers = modifiers
        self._key_widget.update()
        layout_key = self._keyboard_layout.keys.get(scan_code)
        if layout_key:
            key_text = layout_key.to_string(self._keyboard_layout.modifiers_from_modifier_codes(modifiers))
            if modifiers == ModifierCode.NONE:
                self._key_label.setText(key_text)
            else:
                modifier_text: list[str] = []
                for modifier in modifiers:
                    assert modifier.name is not None
                    if modifier != ModifierCode.NONE:
                        modifier_text.append(f'《{modifier.name}》')
                if not scan_code.is_modifier:
                    modifier_text.append(f'《{layout_key.to_string()}》')
                label_text = '+'.join(modifier_text)
                if key_text == layout_key.to_string():
                    self._key_label.setText(label_text)
                else:
                    self._key_label.setText(f"{key_text}     ⟬{label_text}⟭")
        else:
            self._key_label.setText(f"Unknown key: {scan_code.name}")
