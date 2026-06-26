''' Provides configuration for UI components. '''
from __future__ import annotations

import json
from dataclasses import asdict
from typing import TYPE_CHECKING, Any

from PySide6.QtGui import QFont

from .dump_analyzer.section_list import SectionList

if TYPE_CHECKING:
    from .dump_analyzer.byte_info_widget import ByteInfoWidget
    from .dump_analyzer.dump_analyzer import VisibleDetailBytes
    from .dump_analyzer.hex_viewer import HexViewer

class Config:
    _FILE_PATH: str = "config.json"
    _instance: Config

    '''Configuration for UI components.'''
    def __init__(self) -> None:
        self.data: dict[str, Any] = {}

        if hasattr(Config, "_instance"):
            raise Exception("Config is a singleton class. Use Config.instance() to get the instance.")
        try:
            self.data = json.load(open(self._FILE_PATH, "r"))
        except (FileNotFoundError, json.JSONDecodeError):
            self.data = {}

    def _save(self) -> None:
        '''Save the configuration to the file.'''
        with open(self._FILE_PATH, "w") as f:
            json.dump(self.data, f, indent=4)

    @staticmethod
    def instance() -> Config:
        '''Get the singleton instance of the configuration.'''
        if not hasattr(Config, "_instance"):
            Config._instance = Config()
        return Config._instance

    @property
    def last_opened_dump(self) -> str | None:
        '''Get the path of the last opened dump file.'''
        return self.data.get("last_opened_dump")
    @last_opened_dump.setter
    def last_opened_dump(self, path: str) -> None:
        '''Set the path of the last opened dump file.'''
        self.data["last_opened_dump"] = path
        self._save()

    @property
    def hex_viewer_colors(self) -> dict[str, str]:
        '''Get the colors for the hex viewer.'''
        return self.data.get("hex_viewer_colors", {})
    @hex_viewer_colors.setter
    def hex_viewer_colors(self, colors: dict[str, str]) -> None:
        '''Set the colors for the hex viewer.'''
        self.data["hex_viewer_colors"] = colors
        self._save()

    @property
    def sections(self) -> SectionList:
        '''Get the sections defined in the configuration.'''
        if "sections" not in self.data:
            return SectionList(name="M811", relative_start=0, length=0xFFFF)
        section_list = SectionList.from_dict(self.data["sections"])
        if not isinstance(section_list, SectionList):
            raise ValueError("Root section must be a SectionList.")
        return section_list
    @sections.setter
    def sections(self, root: SectionList) -> None:
        '''Set the sections defined in the configuration.'''
        self.data["sections"] = root.to_dict()
        self._save()

    @property
    def visible_detail_bytes(self) -> VisibleDetailBytes:
        '''Get the visible detail bytes defined in the configuration.'''
        from .dump_analyzer.dump_analyzer import VisibleDetailBytes
        if "visible_detail_bytes" not in self.data:
            return VisibleDetailBytes()
        return VisibleDetailBytes(**self.data["visible_detail_bytes"])
    @visible_detail_bytes.setter
    def visible_detail_bytes(self, details: VisibleDetailBytes) -> None:
        '''Set the visible detail bytes defined in the configuration.'''
        self.data["visible_detail_bytes"] = asdict(details)
        self._save()

    @property
    def visible_details(self) -> set[ByteInfoWidget.Elements]:
        '''Get the visible details defined in the configuration.'''
        from .dump_analyzer.byte_info_widget import ByteInfoWidget
        defaults = {ByteInfoWidget.Elements.TITLE, ByteInfoWidget.Elements.HEX1, ByteInfoWidget.Elements.DEC1, ByteInfoWidget.Elements.BIN1}
        if "details" not in self.data:
            return defaults
        d: dict[str, bool] = self.data["details"]
        return {element for element in ByteInfoWidget.Elements if d.get(element.name.lower(), element in defaults)}
    @visible_details.setter
    def visible_details(self, details: set[ByteInfoWidget.Elements]) -> None:
        '''Set the visible details defined in the configuration.'''
        from .dump_analyzer.byte_info_widget import ByteInfoWidget
        d: dict[str, bool] = {}
        for element in ByteInfoWidget.Elements:
            d[element.name.lower()] = element in details
        self.data["details"] = d
        self._save()

    @property
    def encoding(self) -> str:
        '''Get the encoding defined in the configuration.'''
        return self.data.get("encoding", "cp437")
    @encoding.setter
    def encoding(self, encoding: str) -> None:
        '''Set the encoding defined in the configuration.'''
        self.data["encoding"] = encoding
        self._save()

    @property
    def hex_viewer_line_width(self) -> tuple[HexViewer.LineWidth, int | None]:
        '''Get the line width defined in the configuration.'''
        from .dump_analyzer.hex_viewer import HexViewer
        if "hex_viewer_line_width" not in self.data:
            return (HexViewer.LineWidth.POWER_OF_TWO, None)
        value = self.data["hex_viewer_line_width"]
        if isinstance(value, int):
            return (HexViewer.LineWidth.FIXED, value)
        try:
            return (HexViewer.LineWidth[value], None)
        except KeyError:
            raise ValueError(f"Invalid hex_viewer_line_width value: {value}")
    @hex_viewer_line_width.setter
    def hex_viewer_line_width(self, value: HexViewer.LineWidth | int) -> None:
        '''Set the line width defined in the configuration.'''
        from .dump_analyzer.hex_viewer import HexViewer
        if isinstance(value, HexViewer.LineWidth):
            if value == HexViewer.LineWidth.FIXED:
                raise ValueError("LineWidth.FIXED must be set with an integer value.")
            self.data["hex_viewer_line_width"] = value.name
        else:
            self.data["hex_viewer_line_width"] = value
        self._save()

    @property
    def hex_viewer_font(self) -> QFont:
        '''Get the font defined in the configuration.'''
        if "hex_viewer_font" not in self.data:
            return QFont()
        font = QFont()
        font.fromString(self.data["hex_viewer_font"])
        return font
    @hex_viewer_font.setter
    def hex_viewer_font(self, font: QFont) -> None:
        '''Set the font defined in the configuration.'''
        self.data["hex_viewer_font"] = font.toString()
        self._save()
