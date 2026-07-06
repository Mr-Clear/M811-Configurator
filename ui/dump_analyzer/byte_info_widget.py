#! /usr/bin/env python3
''' Widget to show information about a byte in the dump. '''

from enum import Enum

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QStackedWidget, QWidget

from ..config import Config


class ByteInfoWidget(QWidget):
    class Elements(Enum):
        '''Enum for the elements of the byte info widget.'''
        TITLE = 1
        ADDRESS = 2
        HEX1 = 3
        DEC1 = 4
        BIN1 = 5
        HEX2 = 6
        DEC2 = 7
        BIN2 = 8
        HEX4 = 9
        DEC4 = 10
        BIN4 = 11
        ASCII = 12
        UTF8 = 13
        UTF16 = 14

        def __str__(self) -> str:
            E = ByteInfoWidget.Elements
            match self:
                case E.TITLE:
                    return "Title"
                case E.ADDRESS:
                    return "Address"
                case E.HEX1:
                    return "Hex Value"
                case E.DEC1:
                    return "Decimal Value"
                case E.BIN1:
                    return "Binary Value"
                case E.HEX2:
                    return "2 Byte Hex Value"
                case E.DEC2:
                    return "2 Byte Decimal Value"
                case E.BIN2:
                    return "2 Byte Binary Value"
                case E.HEX4:
                    return "4 Byte Hex Value"
                case E.DEC4:
                    return "4 Byte Decimal Value"
                case E.BIN4:
                    return "4 Byte Binary Value"
                case E.ASCII:
                    return "ASCII Value"
                case E.UTF8:
                    return "UTF-8 Value"
                case E.UTF16:
                    return "UTF-16 Value"

        def __repr__(self) -> str:
            E = ByteInfoWidget.Elements
            match self:
                case E.TITLE:
                    return ""
                case E.ADDRESS:
                    return "Address"
                case E.HEX1:
                    return "Hex"
                case E.DEC1:
                    return "Dec"
                case E.BIN1:
                    return "Bin"
                case E.HEX2:
                    return "Hex2"
                case E.DEC2:
                    return "Dec2"
                case E.BIN2:
                    return "Bin2"
                case E.HEX4:
                    return "Hex4"
                case E.DEC4:
                    return "Dec4"
                case E.BIN4:
                    return "Bin4"
                case E.ASCII:
                    return "ASCII"
                case E.UTF8:
                    return "UTF-8"
                case E.UTF16:
                    return "UTF-16"

    def __init__(self, title: str, title_width: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._elements: dict[ByteInfoWidget.Elements, tuple[QWidget, QLabel]] = {}

        monospace_font = self.font()
        monospace_font.setFamily("Courier")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._title_label = QLabel(title, self)
        self._title_label.setFixedWidth(title_width)
        layout.addWidget(self._title_label)
        self._elements[ByteInfoWidget.Elements.TITLE] = (self._title_label, self._title_label)
        self._stack = QStackedWidget(self)
        layout.addWidget(self._stack)
        self._stack_none = QLabel("None")
        self._stack.addWidget(self._stack_none)
        self._stack.setCurrentWidget(self._stack_none)
        self._stack_byte = QWidget()
        self._stack.addWidget(self._stack_byte)
        byte_layout = QHBoxLayout(self._stack_byte)
        byte_layout.setContentsMargins(0, 0, 0, 0)
        byte_layout.setSpacing(8)

        for element in ByteInfoWidget.Elements:
            if element == ByteInfoWidget.Elements.TITLE:
                continue

            container = QWidget()
            value_layout = QHBoxLayout(container)
            value_layout.setContentsMargins(0, 0, 0, 0)
            value_layout.addWidget(QLabel(repr(element) + ':'))

            value_label = QLabel(self.format_byte(element, None, memoryview(b'')), self)
            value_label.setFont(monospace_font)
            value_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            value_label.setFrameStyle(QLabel.Shape.Panel | QLabel.Shadow.Raised)

            value_layout.addWidget(value_label)
            byte_layout.addWidget(container)
            self._elements[element] = (container, value_label)

        layout.addStretch(1)

        self.set_visible_elements(Config.instance().visible_details)

    def set_byte(self, byte_index: int | None, data: memoryview) -> None:
        '''Set the displayed byte information.'''
        if byte_index is None:
            self._stack.setCurrentWidget(self._stack_none)
            return
        self._stack.setCurrentWidget(self._stack_byte)
        for element, (container, value_label) in self._elements.items():
            if container is self._title_label:
                continue
            value_label.setText(self.format_byte(element, byte_index, data))

    def set_title_width(self, width: int) -> None:
        '''Set the width of the title label.'''
        self._title_label.setFixedWidth(width)

    def set_visible_elements(self, view_options: set[Elements]) -> None:
        '''Set the view options for the widget.'''
        for element, (container, _) in self._elements.items():
            container.setVisible(element in view_options)

    def read_byte(self, byte_index: int | None, length: int, data: memoryview) -> int | None:
        '''Read a byte value from the data.'''
        from ui.dump_analyzer.dump_analyzer import IntegerFormat
        if byte_index is None or byte_index + length > len(data):
            return None
        value = 0
        if Config.instance().integer_format == IntegerFormat.LITTLE_ENDIAN:
            for i in range(length):
                value |= data[byte_index + i] << (8 * i)
        else:
            for i in range(length):
                value |= data[byte_index + i] << (8 * (length - 1 - i))
        return value

    def format_byte(self, element: Elements, byte_index: int | None, data: memoryview) -> str:
        '''Format a byte value as a string.'''
        if byte_index is None or byte_index >= len(data):
            return "N/A"
        E = ByteInfoWidget.Elements
        match element:
            case E.TITLE:
                raise ValueError("Cannot format TITLE element.")
            case E.ADDRESS:
                return f'0x{byte_index:04X}'
            case E.HEX1:
                return f'0x{data[byte_index]:02X}'
            case E.DEC1:
                return f'{data[byte_index]:3d}'
            case E.BIN1:
                return f'{data[byte_index]:08b}'
            case E.HEX2:
                v = self.read_byte(byte_index, 2, data)
                return f'0x{v:04X}' if v is not None else "N/A  "
            case E.DEC2:
                v = self.read_byte(byte_index, 2, data)
                return f'{v:5d}' if v is not None else "N/A  "
            case E.BIN2:
                if byte_index + 1 < len(data):
                    byte2_value = data[byte_index + 1] + (data[byte_index] << 8)
                    return f'{byte2_value:016b}'
                else:
                    return "N/A" + " " * 13
            case E.HEX4:
                v = self.read_byte(byte_index, 4, data)
                return f'0x{v:08X}' if v is not None else "N/A      "
            case E.DEC4:
                v = self.read_byte(byte_index, 4, data)
                return f'{v:10d}' if v is not None else "N/A      "
            case E.BIN4:
                if byte_index + 3 < len(data):
                    byte4_value = (data[byte_index + 3] << 24) + (data[byte_index + 2] << 16) + (data[byte_index + 1] << 8) + data[byte_index]
                    return f'{byte4_value:032b}'
                else:
                    return "N/A" + " " * 29
            case E.ASCII:
                byte_value = data[byte_index]
                return chr(byte_value) if 32 <= byte_value <= 126 else '.'
            case E.UTF8:
                # For UTF-8, we need to decode the bytes starting at byte_index
                # and find the first valid UTF-8 character.
                try:
                    # Find the end of the UTF-8 character starting at byte_index
                    for end in range(byte_index + 1, min(byte_index + 4, len(data) + 1)):
                        char_bytes = data[byte_index:end].tobytes()
                        char = char_bytes.decode('utf-8')
                        return char
                except UnicodeDecodeError:
                    return "�"  # Replacement character for invalid UTF-8
                return "N/A"
            case E.UTF16:
                # For UTF-16, we need to decode the bytes starting at byte_index
                # and find the first valid UTF-16 character.
                try:
                    # UTF-16 requires at least 2 bytes
                    if byte_index + 1 < len(data):
                        char_bytes = data[byte_index:byte_index + 2].tobytes()
                        char = char_bytes.decode('utf-16le')  # Assuming little-endian
                        return char
                except UnicodeDecodeError:
                    return "�"  # Replacement character for invalid UTF-16
                return "N/A"
