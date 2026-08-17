from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from .mouse_data.mouse_definition import MouseDefinition
from .mouse_data import MouseData
from .usb_connection import UsbConnection

class MouseType(Enum):
    '''Enumeration of supported mouse types, identified by USB product ID.'''
    M901 = 0xfc02
    M990 = 0xfc0f
    M709 = 0xfc2a
    M702 = 0xfc2f
    M711 = 0xfc30
    M602 = 0xfc38
    M607 = 0xfc38
    M715 = 0xfc39
    M921 = 0xfc40
    M990_RGB = 0xfc41
    M909 = 0xfc42
    M802 = 0xfc42
    M910 = 0xfc49
    M908 = 0xfc4d
    M719 = 0xfc4f
    M721 = 0xfc5c
    M801 = 0xfc56
    M808 = 0xfc5f
    M612 = 0xfc61
    M811 = 0xfc6d

    @staticmethod
    def from_product_id(product_id: int) -> "MouseType | None":
        '''Get the MouseType corresponding to a given USB product ID, or None if not recognized.'''
        for mouse_type in MouseType:
            if mouse_type.value == product_id:
                return mouse_type
        return None

@dataclass
class Mouse:
    '''Represents a mouse with its type, definition, and data.'''
    definition: MouseDefinition
    data: MouseData
    connection: UsbConnection
    data_on_device: bytes | None = None

    @property
    def type(self) -> MouseType:
        '''Get the MouseType corresponding to this mouse's USB product ID.'''
        t = MouseType.from_product_id(self.connection.dev.idProduct)
        if t is None:
            raise ValueError(f"Unsupported mouse product ID: {self.connection.dev.idProduct}")
        return t
