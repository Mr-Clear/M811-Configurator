#! /usr/bin/env python3
''' Window to show and analyze dumps from the mouse. '''

import json
import logging
import sys
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Callable

from PySide6.QtGui import QAction, Qt
from PySide6.QtWidgets import (QApplication, QCheckBox, QColorDialog,
                               QFileDialog, QInputDialog, QMainWindow,
                               QMessageBox, QScrollArea, QVBoxLayout, QWidget,
                               QWidgetAction)

from ui.config import Config

from .byte_info_widget import ByteInfoWidget
from .hex_viewer import HexViewer
from .section_list import SectionList
from .sections_widget import SectionsWidget

logger = logging.getLogger(__name__)

@dataclass
class VisibleDetailBytes:
    hovered: bool = True
    selected: bool = True
    pinned: set[int] = field(default_factory=lambda: set())

class DumpAnalyzer (QMainWindow):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._config = Config.instance()
        self._data: bytes = bytes()
        self._root_section: SectionList = self._config.sections
        self._hex_viewer: HexViewer
        self._sections_widget: SectionsWidget
        self._visible_detail_bytes: VisibleDetailBytes = self._config.visible_detail_bytes
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

        infos = ["Hovered:", "Selected:"]
        max_title_width = max(self.fontMetrics().horizontalAdvance(info) for info in infos) + 2
        self._info_widgets: dict[str, ByteInfoWidget] = {}
        for info in infos:
            info_widget = ByteInfoWidget(info, max_title_width, self)
            layout.addWidget(info_widget, 0)
            self._info_widgets[info] = info_widget
        self._details_byte_hovered = self._info_widgets["Hovered:"]
        self._details_byte_hovered.setVisible(self._visible_detail_bytes.hovered)
        self._details_byte_selected = self._info_widgets["Selected:"]
        self._details_byte_selected.setVisible(self._visible_detail_bytes.selected)
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
        m.view_details = m.view.addMenu("Details")
        def add_detail_action(name: str, attr: str, on_click: Callable[[bool], None] | None) -> None:
            action = m.view_details.addAction(name)
            action.setCheckable(True)
            action.setChecked(getattr(self._visible_detail_bytes, attr, False))
            if on_click is not None:
                action.toggled.connect(on_click)
        m.view_details_hovered = add_detail_action("Hovered Byte", "hovered", self._on_details_hovered_toggled)
        m.view_details_selected = add_detail_action("Selected Byte", "selected", self._on_details_selected_toggled)
        m.view_details.addSeparator()
        visible_elements = self._config.visible_details
        for element in ByteInfoWidget.Elements:
            container = QWidget()
            container_layout = QVBoxLayout(container)
            container_layout.setContentsMargins(10, 1, 10, 1)
            checkbox = QCheckBox(str(element))
            container_layout.addWidget(checkbox)
            action = QWidgetAction(m.view_details)
            action.setDefaultWidget(container)
            checkbox.setChecked(element in visible_elements)
            def on_action_click(checked: bool, element: ByteInfoWidget.Elements = element) -> None:
                visible_elements = self._config.visible_details
                if checked:
                    visible_elements.add(element)
                else:
                    visible_elements.discard(element)
                self._config.visible_details = visible_elements
                for info_widget in self._info_widgets.values():
                    info_widget.set_visible_elements(visible_elements)
            checkbox.toggled.connect(on_action_click)
            m.view_details.addAction(action)

        m.view_encoding = m.view.addMenu("Encoding")
        for encoding, name in encodings:
            action = m.view_encoding.addAction(name)
            action.setCheckable(True)
            action.setChecked(self._config.encoding == encoding)
            def on_click(checked: bool) -> None:
                if checked:
                    self._config.encoding = encoding
                    for act in m.view_encoding.actions():
                        if act != action:
                            act.setChecked(False)
                    self._config.visible_detail_bytes = self._visible_detail_bytes
                    self._hex_viewer.set_encoding(encoding)
            action.toggled.connect(on_click)

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

        def set_line_width(line_width: HexViewer.LineWidth) -> None:
            if line_width == HexViewer.LineWidth.FIXED:
                value, ok = QInputDialog.getInt(self, "Set Fixed Line Width", "Enter fixed line width:")
                if not ok:
                    return
                self._config.hex_viewer_line_width = value
                self._hex_viewer.line_width = value
            else:
                self._config.hex_viewer_line_width = line_width
                self._hex_viewer.line_width = line_width
            for action in m_view_linewidth.actions():
                action.setChecked(action.text() == line_width.name.replace("_", " ").title())
        m_view_linewidth = m.view.addMenu("Line Width")
        m_view_linewidth_fixed = m_view_linewidth.addAction("Fixed")
        m_view_linewidth_fixed.setCheckable(True)
        m_view_linewidth_fixed.setChecked(self._config.hex_viewer_line_width[0] == HexViewer.LineWidth.FIXED)
        m_view_linewidth_fixed.triggered.connect(lambda: set_line_width(HexViewer.LineWidth.FIXED))
        m_view_linewidth_any = m_view_linewidth.addAction("Free")
        m_view_linewidth_any.setCheckable(True)
        m_view_linewidth_any.setChecked(self._config.hex_viewer_line_width[0] == HexViewer.LineWidth.ANY)
        m_view_linewidth_any.triggered.connect(lambda: set_line_width(HexViewer.LineWidth.ANY))
        m_view_linewidth_power_of_two = m_view_linewidth.addAction("Power of Two")
        m_view_linewidth_power_of_two.setCheckable(True)
        m_view_linewidth_power_of_two.setChecked(self._config.hex_viewer_line_width[0] == HexViewer.LineWidth.POWER_OF_TWO)
        m_view_linewidth_power_of_two.triggered.connect(lambda: set_line_width(HexViewer.LineWidth.POWER_OF_TWO))
        m_view_linewidth.addSeparator()

        self._menues = m

    def _on_details_hovered_toggled(self, checked: bool) -> None:
        '''Handle toggling of the hovered byte details view option.'''
        self._visible_detail_bytes.hovered = checked
        self._details_byte_hovered.setVisible(checked)
        self._config.visible_detail_bytes = self._visible_detail_bytes
        self._details_byte_hovered.setVisible(self._visible_detail_bytes.hovered)

    def _on_details_selected_toggled(self, checked: bool) -> None:
        '''Handle toggling of the selected byte details view option.'''
        self._visible_detail_bytes.selected = checked
        self._details_byte_selected.setVisible(checked)
        self._config.visible_detail_bytes = self._visible_detail_bytes
        self._details_byte_selected.setVisible(self._visible_detail_bytes.selected)

    def _on_byte_hovered(self, byte_index: int) -> None:
        '''Handle byte hovered event.'''
        self._details_byte_hovered.set_byte(byte_index, self._hex_viewer.data)

    def _on_byte_hovered_leave(self) -> None:
        '''Handle byte hover leave event.'''
        self._details_byte_hovered.set_byte(None, memoryview(b''))

    def _on_byte_clicked(self, byte_index: int) -> None:
        '''Handle byte clicked event.'''
        self._details_byte_selected.set_byte(byte_index, self._hex_viewer.data)

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

encodings = [
    ("ascii", "ASCII"),
    ("iso8859_2", "ISO-8859-2 (Central and Eastern Europe)"),
    ("iso8859_3", "ISO-8859-3 (Esperanto, Maltese)"),
    ("iso8859_4", "ISO-8859-4 (Baltic languages)"),
    ("iso8859_5", "ISO-8859-5 (Cyrillic)"),
    ("iso8859_6", "ISO-8859-6 (Arabic)"),
    ("iso8859_7", "ISO-8859-7 (Greek)"),
    ("iso8859_8", "ISO-8859-8 (Hebrew)"),
    ("iso8859_9", "ISO-8859-9 (Turkish)"),
    ("iso8859_10", "ISO-8859-10 (Nordic languages)"),
    ("iso8859_11", "ISO-8859-11 (Thai)"),
    ("iso8859_13", "ISO-8859-13 (Baltic languages)"),
    ("iso8859_14", "ISO-8859-14 (Celtic languages)"),
    ("iso8859_15", "ISO-8859-15 (Western European languages)"),
    ("iso8859_16", "ISO-8859-16 (South-Eastern European languages)"),
    ("cp437", "Code Page 437 (Original IBM PC)"),
    ("cp850", "Code Page 850 (Western European languages)"),
    ("cp852", "Code Page 852 (Central and Eastern Europe)"),
    ("cp855", "Code Page 855 (Cyrillic)"),
    ("cp857", "Code Page 857 (Turkish)"),
    ("cp860", "Code Page 860 (Portuguese)"),
    ("cp861", "Code Page 861 (Icelandic)"),
    ("cp862", "Code Page 862 (Hebrew)"),
    ("cp863", "Code Page 863 (French Canadian)"),
    ("cp864", "Code Page 864 (Arabic)"),
    ("cp865", "Code Page 865 (Nordic languages)"),
    ("cp866", "Code Page 866 (Cyrillic)"),
    ("cp869", "Code Page 869 (Greek)"),
    ("cp1250", "Windows-1250 (Central and Eastern Europe)"),
    ("cp1251", "Windows-1251 (Cyrillic)"),
    ("cp1252", "Windows-1252 (Western European languages)"),
    ("cp1253", "Windows-1253 (Greek)"),
    ("cp1254", "Windows-1254 (Turkish)"),
    ("cp1255", "Windows-1255 (Hebrew)"),
    ("cp1256", "Windows-1256 (Arabic)"),
    ("cp1257", "Windows-1257 (Baltic languages)"),
    ("cp1258", "Windows-1258 (Vietnamese)")
]

if __name__ == "__main__":
    raise SystemExit(start_app())
