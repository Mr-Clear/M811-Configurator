#!/usr/bin/env python3
import json

from ui.dump_analyzer.sections.list_section import ListSection, Section
from ui.redragon_mouse import MouseData
from pprint import pprint as pp

with open("M811.json", "r") as f:
    section_list = Section.from_dict(json.load(f))
assert isinstance(section_list, ListSection)

with open("M811.dump", "rb") as f:
    data = f.read()
mouse_data = MouseData(section_list, data)
pp(mouse_data.to_json())
