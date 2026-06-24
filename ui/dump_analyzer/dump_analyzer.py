#! /usr/bin/env python3
''' Window to show and analyze dumps from the mouse. '''

import json
import logging
import sys

from PySide6.QtGui import QAction
from PySide6.QtWidgets import (QApplication, QFileDialog, QMainWindow,
                               QMessageBox, QScrollArea, QVBoxLayout, QWidget)

from ui.config import Config

from .byte_info_widget import ByteInfoWidget
from .hex_viewer import HexViewer
from .section_list import SectionList
from .sections_widget import SectionsWidget

logger = logging.getLogger(__name__)

class DumpAnalyzer (QMainWindow):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._config = Config.instance()
        self._data: bytes = bytes()
        self._root_section: SectionList = self._config.sections
        self._hex_viewer: HexViewer
        self._sections_widget: SectionsWidget
        self._menues: SimpleNamespace

        self._init_ui()
        self._hex_viewer.set_root_section(self._root_section)

        if self._config.last_opened_dump:
            try:
                with open(self._config.last_opened_dump, "rb") as f:
                    self._data = f.read()
                self._hex_viewer.data = self._data
            except Exception as e:
                logger.error(f"Failed to load last opened dump: {e}")
        if not hasattr(self, "_data") or not self._data:
            self._data = bytes(i % 256 for i in range(0x1C00))
        self._hex_viewer.data = self._data

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

        self._hex_viewer = HexViewer()
        self._hex_viewer.data = self._data
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
        self._sections_widget.sections_changed.connect(self._on_section_changed)
        layout.addWidget(self._sections_widget, 0)

        self._init_menu()

    def _init_menu(self) -> None:
        '''Initialize the menu bar.'''
        m = SimpleNamespace()
        m.file = self.menuBar().addMenu("File")
        m.file.aboutToShow.connect(self._on_file_menu_show)
        m.file_open = m.file.addAction("Open Dump...")
        m.file_open.triggered.connect(self._open_dump)
        m.file_read_usb = m.file.addAction("Read from USB")
        m.file_read_usb.triggered.connect(self._read_from_usb)
        m.file_write_usb = m.file.addAction("Write to USB")
        m.file_write_usb.triggered.connect(self._write_to_usb)
        m.file.addSeparator()
        m.file_load_sections = m.file.addAction("Load Sections...")
        m.file_load_sections.triggered.connect(self._load_sections)
        m.file_save_sections = m.file.addAction("Save Sections...")
        m.file_save_sections.triggered.connect(self._save_sections)

        m.view = self.menuBar().addMenu("View")

        m.view_encoding = m.view.addMenu("Encoding")
        def add_encoding_action(encoding: str, name: str) -> QAction:
            action = m.view_encoding.addAction(name)
            action.setCheckable(True)
            action.setChecked(self._config.encoding == encoding)
            def on_click(checked: bool) -> None:
                if checked:
                    self._config.encoding = encoding
                    for act in m.view_encoding.actions():
                        if act != action:
                            act.setChecked(False)
                    self._config.view_options = self._view_options
                    self._hex_viewer.set_encoding(encoding)
            action.toggled.connect(on_click)
            return action
        add_encoding_action("ascii", "ASCII")
        add_encoding_action("iso8859_2", "ISO-8859-2 (Central and Eastern Europe)")
        add_encoding_action("iso8859_3", "ISO-8859-3 (Esperanto, Maltese)")
        add_encoding_action("iso8859_4", "ISO-8859-4 (Baltic languages)")
        add_encoding_action("iso8859_5", "ISO-8859-5 (Cyrillic)")
        add_encoding_action("iso8859_6", "ISO-8859-6 (Arabic)")
        add_encoding_action("iso8859_7", "ISO-8859-7 (Greek)")
        add_encoding_action("iso8859_8", "ISO-8859-8 (Hebrew)")
        add_encoding_action("iso8859_9", "ISO-8859-9 (Turkish)")
        add_encoding_action("iso8859_10", "ISO-8859-10 (Nordic languages)")
        add_encoding_action("iso8859_11", "ISO-8859-11 (Thai)")
        add_encoding_action("iso8859_13", "ISO-8859-13 (Baltic languages)")
        add_encoding_action("iso8859_14", "ISO-8859-14 (Celtic languages)")
        add_encoding_action("iso8859_15", "ISO-8859-15 (Western European languages)")
        add_encoding_action("iso8859_16", "ISO-8859-16 (South-Eastern European languages)")
        add_encoding_action("cp437", "Code Page 437 (Original IBM PC)")
        add_encoding_action("cp850", "Code Page 850 (Western European languages)")
        add_encoding_action("cp852", "Code Page 852 (Central and Eastern Europe)")
        add_encoding_action("cp855", "Code Page 855 (Cyrillic)")
        add_encoding_action("cp857", "Code Page 857 (Turkish)")
        add_encoding_action("cp860", "Code Page 860 (Portuguese)")
        add_encoding_action("cp861", "Code Page 861 (Icelandic)")
        add_encoding_action("cp862", "Code Page 862 (Hebrew)")
        add_encoding_action("cp863", "Code Page 863 (French Canadian)")
        add_encoding_action("cp864", "Code Page 864 (Arabic)")
        add_encoding_action("cp865", "Code Page 865 (Nordic languages)")
        add_encoding_action("cp866", "Code Page 866 (Cyrillic)")
        add_encoding_action("cp869", "Code Page 869 (Greek)")
        add_encoding_action("cp1250", "Windows-1250 (Central and Eastern Europe)")
        add_encoding_action("cp1251", "Windows-1251 (Cyrillic)")
        add_encoding_action("cp1252", "Windows-1252 (Western European languages)")
        add_encoding_action("cp1253", "Windows-1253 (Greek)")
        add_encoding_action("cp1254", "Windows-1254 (Turkish)")
        add_encoding_action("cp1255", "Windows-1255 (Hebrew)")
        add_encoding_action("cp1256", "Windows-1256 (Arabic)")
        add_encoding_action("cp1257", "Windows-1257 (Baltic languages)")
        add_encoding_action("cp1258", "Windows-1258 (Vietnamese)")

        m.view_colors = m.view.addMenu("Colors")
        def add_color_action(name: str, color: HexViewer.Colors) -> QAction:
            action = m.view_colors.addAction(name)
            color_name = color.name.lower()
            action.setChecked(self._config.hex_viewer_colors.get(color_name, "") != "")
            def on_click() -> None:
                old_color = self._config.hex_viewer_colors.get(color_name, "")
                new_color = QColorDialog.getColor(old_color, self, f"Select color for {name}")
                if new_color and new_color.isValid():
                    self._hex_viewer.set_color(color, new_color)
            action.triggered.connect(on_click)
            return action
        for color in HexViewer.Colors:
            add_color_action(color.name.capitalize(), color)


        self._menues = m
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

    def _on_file_menu_show(self) -> None:
        '''Update the "File" menu actions based on the current state.'''
        hex_changed = self._hex_viewer.data != memoryview(self._data)
        self._menues.file_write_usb.setEnabled(hex_changed)

    def _open_dump(self) -> None:
        '''Open a dump file.'''
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Dump", "", "All Files (*)")
        if file_name:
            with open(file_name, "rb") as f:
                self._data = f.read()
            self._hex_viewer.data = self._data
            self._config.last_opened_dump = file_name

    def _read_from_usb(self) -> None:
        '''Read dump data from the USB device.'''
        try:
            from .usb import RedragonMouse
            mouse = RedragonMouse()
            self._data = mouse.read_all()
            self._hex_viewer.data = self._data
        except Exception as e:
            logger.exception(f"Failed to read from USB: {e}")
            QMessageBox.critical(self, "Error", f"Failed to read from USB: {e}")

    def _write_to_usb(self) -> None:
        '''Write modified dump data to the USB device.'''
        try:
            from .usb import RedragonMouse
            mouse = RedragonMouse()
            mouse.write_diff(self._data, self._hex_viewer.data)
            QMessageBox.information(self, "Success", "Data successfully written to USB device.")
        except Exception as e:
            logger.exception(f"Failed to write to USB: {e}")
            QMessageBox.critical(self, "Error", f"Failed to write to USB: {e}")

    def _load_sections(self) -> None:
        '''Load sections from a JSON file.'''
        file_name, _ = QFileDialog.getOpenFileName(self, "Load Sections", "", "JSON Files (*.json)")
        if file_name:
            try:
                with open(file_name, "r") as f:
                    section_list = SectionList.from_dict(json.load(f))
                assert isinstance(section_list, SectionList)
                self._sections_widget.root_section = section_list
            except Exception as e:
                logger.error(f"Failed to load sections: {e}")
                QMessageBox.critical(self, "Error", f"Failed to load sections: {e}")

    def _save_sections(self) -> None:
        '''Save sections to a JSON file.'''
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Sections", "", "JSON Files (*.json)")
        if file_name:
            try:
                with open(file_name, "w") as f:
                    json.dump(self._sections_widget.root_section.to_dict(), f, indent=4)
            except Exception as e:
                logger.error(f"Failed to save sections: {e}")
                QMessageBox.critical(self, "Error", f"Failed to save sections: {e}")

    def _on_section_changed(self) -> None:
        '''Handle changes to the section information.'''
        self._config.sections = self._sections_widget.root_section
        self._hex_viewer.repaint()

def start_app() -> int:
    '''Creates the main window and starts the application event loop.'''
    app = QApplication(sys.argv)
    window = DumpAnalyzer()
    window.show()
    return app.exec()

if __name__ == "__main__":
    raise SystemExit(start_app())
