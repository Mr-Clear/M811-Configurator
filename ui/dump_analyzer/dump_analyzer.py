#! /usr/bin/env python3
''' Window to show and analyze dumps from the mouse. '''

import sys

from PySide6.QtWidgets import (QApplication, QFileDialog, QMainWindow,
                               QScrollArea, QVBoxLayout, QWidget)

from ui.config import Config
from .section import SectionList

from .byte_info_widget import ByteInfoWidget
from .hex_viewer import HexViewer
from .sections_widget import SectionsWidget


class DumpAnalyzer (QMainWindow):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._config = Config.instance()
        self._data: bytes = bytes()
        self._root_section: SectionList = self._config.sections
        self._hex_viewer: HexViewer
        self._sections_widget: SectionsWidget

        self._init_ui()

        if self._config.last_opened_dump:
            try:
                with open(self._config.last_opened_dump, "rb") as f:
                    self._data = f.read()
                self._hex_viewer.set_data(self._data)
            except Exception as e:
                print(f"Failed to load last opened dump: {e}")
        if not hasattr(self, "_data") or not self._data:
            self._data = bytes(i % 256 for i in range(0x1C00))
        self._hex_viewer.set_data(self._data)

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
        layout.addSpacing(4)

        self._sections_widget = SectionsWidget(self._root_section, self)
        layout.addWidget(self._sections_widget, 0)

        self._init_menu()

    def _init_menu(self) -> None:
        '''Initialize the menu bar.'''
        file = self.menuBar().addMenu("File")
        file_open = file.addAction("Open Dump...")
        file_open.triggered.connect(self._open_dump)

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

    def _open_dump(self) -> None:
        '''Open a dump file.'''
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Dump", "", "All Files (*)")
        if file_name:
            with open(file_name, "rb") as f:
                self._data = f.read()
            self._hex_viewer.set_data(self._data)
            self._config.last_opened_dump = file_name

def start_app() -> int:
    '''Creates the main window and starts the application event loop.'''
    app = QApplication(sys.argv)
    window = DumpAnalyzer()
    window.show()
    return app.exec()

if __name__ == "__main__":
    raise SystemExit(start_app())
