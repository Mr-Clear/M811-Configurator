#!/usr/bin/env python3
import json
from pprint import pprint as pp

from ui.dump_analyzer.sections.list_section import ListSection, Section
from ui.mouse_data import MouseData

with open("M811.json", "r") as f:
    section_list = Section.from_dict(json.load(f))
assert isinstance(section_list, ListSection)

with open("M811.dump", "rb") as f:
    data = f.read()
mouse_data = MouseData(section_list, data)
pp(mouse_data.to_json())
