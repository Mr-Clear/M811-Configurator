from __future__ import annotations

import json
import os
from dataclasses import dataclass

from mouse import VENDOR_ID, MouseType
from ui.dump_analyzer.sections.list_section import ListSection


@dataclass
class MouseDefinition:
    """Defines a mouse type"""
    name: str
    vendor_id: int
    product_id: int
    image: str
    buttons: list[str]
    mode_count: int
    macro_count: int
    steps_per_macro: int
    memory_size: int
    data_definition: ListSection

    @classmethod
    def from_file(cls, file_path: str) -> MouseDefinition:
        """Load a mouse definition from a JSON file."""
        with open(file_path, "r") as f:
            data = json.load(f)
        data_definition = ListSection.from_dict(data["sections"])
        assert isinstance(data_definition, ListSection), "The 'sections' field must be a ListSection."
        return cls(
            name=data["mouse_name"],
            vendor_id=int(data["vendor_id"], 16),
            product_id=int(data["product_id"], 16),
            image=data["image"],
            buttons=data["buttons"],
            mode_count=data["mode_count"],
            macro_count=data["macro_count"],
            steps_per_macro=data["steps_per_macro"],
            memory_size=data["memory_size"],
            data_definition=data_definition,
        )

    @classmethod
    def from_device(cls, vendor_id: int, product_id: int) -> MouseDefinition:
        """Load a mouse definition from a JSON file based on the vendor and product IDs."""
        if vendor_id != VENDOR_ID:
            raise ValueError(f"Unsupported vendor ID: {vendor_id:#04x}")
        mouse_type = MouseType.from_product_id(product_id)
        if mouse_type is None:
            raise ValueError(f"Unsupported product ID: {product_id:#04x}")
        file_path = f"{mouse_type.name}.json"
        if not os.path.exists(file_path):
            raise ValueError(f"Mouse definition for {mouse_type.name} not found.")
        return cls.from_file(file_path)

    @property
    def mouse_type(self) -> MouseType:
        """Get the MouseType corresponding to this mouse definition."""
        t = MouseType.from_product_id(self.product_id)
        if t is None:
            raise ValueError(f"Product ID {self.product_id} is unknown.")
        return t
