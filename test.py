#!/usr/bin/env python3
from ui.redragon_mouse import MouseDefinition
from ui.dump_analyzer.sections.list_section import ListSection
import json

with open("M811.json", "r") as f:
    section_list = ListSection.from_dict(json.load(f))
mouse_definition = MouseDefinition(section_list)

print(f"Mouse definition: {mouse_definition._active_mode.absolute_start:04x}")
