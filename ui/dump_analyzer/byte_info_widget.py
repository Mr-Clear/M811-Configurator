#! /usr/bin/env python3
''' Widget to show information about a byte in the dump. '''

import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel,
                               QStackedWidget, QWidget)


class ByteInfoWidget(QWidget):
    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        monospace_font = self.font()
        monospace_font.setFamily("Courier")

        def make_value_label(text: str) -> QLabel:
            label = QLabel(text)
            label.setFont(monospace_font)
            label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            label.setFrameStyle(QLabel.Shape.Panel | QLabel.Shadow.Raised)
            return label

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._title_label = QLabel(title, self)
        layout.addWidget(self._title_label)
        self._stack = QStackedWidget(self)
        layout.addWidget(self._stack)
        self._stack_none = QLabel("None")
        self._stack.addWidget(self._stack_none)
        self._stack.setCurrentWidget(self._stack_none)
        self._stack_byte = QWidget()
        self._stack.addWidget(self._stack_byte)
        byte_layout = QHBoxLayout(self._stack_byte)
        byte_layout.setContentsMargins(0, 0, 0, 0)
        byte_layout.addWidget(QLabel("Address:"))
        self._address_label = make_value_label("0x0000")
        byte_layout.addWidget(self._address_label)
        byte_layout.addWidget(QLabel("Hex:"))
        self._value_label = make_value_label("0x00")
        byte_layout.addWidget(self._value_label)
        byte_layout.addWidget(QLabel("Dec:"))
        self._dec_label = make_value_label("  0")
        byte_layout.addWidget(self._dec_label)
        byte_layout.addWidget(QLabel("ASCII:"))
        self._ascii_label = make_value_label(".")
        byte_layout.addWidget(self._ascii_label)
        byte_layout.addWidget(QLabel("Hex2:"))
        self._hex2_label = make_value_label("0x0000")
        byte_layout.addWidget(self._hex2_label)
        byte_layout.addWidget(QLabel("Dec2:"))
        self._dec2_label = make_value_label("    0")
        byte_layout.addWidget(self._dec2_label)
        layout.addStretch(1)

    def set_byte(self, byte_index: int | None, byte_value: int | None, byte2_value: int | None) -> None:
        '''Set the displayed byte information.'''
        if byte_index is None or byte_value is None:
            self._stack.setCurrentWidget(self._stack_none)
            return
        self._address_label.setText(f'0x{byte_index:04X}')
        self._value_label.setText(f'0x{byte_value:02X}')
        self._dec_label.setText(f'{byte_value:3d}')
        ascii_char = chr(byte_value) if 32 <= byte_value <= 126 else '.'
        self._ascii_label.setText(ascii_char)
        if byte2_value is not None:
            self._hex2_label.setText(f'0x{byte2_value:04X}')
            self._dec2_label.setText(f'{byte2_value:5d}')
        else:
            self._hex2_label.setText('   N/A')
            self._dec2_label.setText('  N/A')
        self._stack.setCurrentWidget(self._stack_byte)

def start_app() -> int:
    '''Creates the main window and starts the application event loop.'''
    app = QApplication(sys.argv)
    window = DumpAnalyzer()
    window.show()
    return app.exec()

if __name__ == "__main__":
    raise SystemExit(start_app())
