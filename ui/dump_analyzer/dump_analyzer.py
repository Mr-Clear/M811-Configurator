#! /usr/bin/env python3
''' Window to show and analyze dumps from the mouse. '''

import sys

from PySide6.QtWidgets import (QApplication, QMainWindow, QScrollArea,
                               QVBoxLayout, QWidget)

from .byte_info_widget import ByteInfoWidget
from .hex_viewer import HexViewer


class DumpAnalyzer (QMainWindow):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._data: bytes
        self._data = bytes(i % 256 for i in range(0x1C00))
        self._hex_viewer: HexViewer

        self._init_ui()

    def _init_ui(self) -> None:
        '''Initialize the user interface.'''

        self.setWindowTitle("Dump Analyzer")
        self.resize(800, 600)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(1)

        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area, 1)

        self._hex_viewer = HexViewer(self._data)
        self._hex_viewer.byte_hovered.connect(self._on_byte_hovered)
        self._hex_viewer.byte_hovered_leave.connect(self._on_byte_hovered_leave)
        self._hex_viewer.byte_clicked.connect(self._on_byte_clicked)
        scroll_area.setWidget(self._hex_viewer)

        self._hovered_byte_info = ByteInfoWidget("Hovered:", self)
        layout.addWidget(self._hovered_byte_info, 0)
        self._selected_byte_info = ByteInfoWidget("Selected:", self)
        layout.addWidget(self._selected_byte_info, 0)

    def _get_byte_values(self, byte_index: int) -> tuple[int | None, int | None]:
        '''Get the byte value and the next byte value for a given byte index.'''
        if 0 <= byte_index < len(self._data):
            byte_value = self._data[byte_index]
            if byte_index + 1 < len(self._data):
                byte2_value = self._data[byte_index + 1] + (byte_value << 8)
            else:
                byte2_value = None
            return byte_value, byte2_value
        return None, None

    def _on_byte_hovered(self, byte_index: int) -> None:
        '''Handle byte hovered event.'''
        byte_value, byte2_value = self._get_byte_values(byte_index)
        self._hovered_byte_info.set_byte(byte_index, byte_value, byte2_value)

    def _on_byte_hovered_leave(self) -> None:
        '''Handle byte hover leave event.'''
        self._hovered_byte_info.set_byte(None, None, None)

    def _on_byte_clicked(self, byte_index: int) -> None:
        '''Handle byte clicked event.'''
        byte_value, byte2_value = self._get_byte_values(byte_index)
        self._selected_byte_info.set_byte(byte_index, byte_value, byte2_value)

def start_app() -> int:
    '''Creates the main window and starts the application event loop.'''
    app = QApplication(sys.argv)
    window = DumpAnalyzer()
    window.show()
    return app.exec()

if __name__ == "__main__":
    raise SystemExit(start_app())
