''' Provides configuration for UI components. '''
from __future__ import annotations

import json
from typing import Any

from ui.dump_analyzer.section import Section

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
        except FileNotFoundError:
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
    def hex_viewer_colors(self) -> dict[str, str] | None:
        '''Get the colors for the hex viewer.'''
        return self.data.get("hex_viewer_colors")
    @hex_viewer_colors.setter
    def hex_viewer_colors(self, colors: dict[str, str]) -> None:
        '''Set the colors for the hex viewer.'''
        self.data["hex_viewer_colors"] = colors
        self._save()

    @property
    def sections(self) -> Section:
        '''Get the sections defined in the configuration.'''
        if "sections" not in self.data:
            return Section(name="Root", start=0, size=0xFFFF)
        return Section.from_dict(self.data["sections"])
    @sections.setter
    def sections(self, root: Section) -> None:
        '''Set the sections defined in the configuration.'''
        self.data["sections"] = root.to_dict()
        self._save()
