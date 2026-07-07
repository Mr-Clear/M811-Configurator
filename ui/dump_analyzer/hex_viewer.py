''' Widget for displaying binary data in a hex viewer format. '''
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import cached_property
from typing import Sequence

from PySide6.QtCore import QEvent, QPoint, QPointF, QRect, QSize, QTimer, Signal
from PySide6.QtGui import (QColor, QCursor, QFont, QFontMetrics, QKeyEvent,
                           QMouseEvent, QPainter, QPaintEvent, QPalette,
                           QResizeEvent, QShowEvent, Qt, QWheelEvent)
from PySide6.QtWidgets import QScrollArea, QWidget

from ui.config import Config

from .sections.section import Section
from .sections.list_section import ListSection

NUMBER_KEYS = set(range(Qt.Key.Key_0, Qt.Key.Key_9 + 1))
LETTER_KEYS = set(range(Qt.Key.Key_A, Qt.Key.Key_F + 1))
HEX_EDIT_KEYS = NUMBER_KEYS.union(LETTER_KEYS)

def _blend_color(color1: QColor, color2: QColor, ratio: float = 0.5) -> QColor:
    r = int(color1.red() * (1 - ratio) + color2.red() * ratio)
    g = int(color1.green() * (1 - ratio) + color2.green() * ratio)
    b = int(color1.blue() * (1 - ratio) + color2.blue() * ratio)
    a = int(color1.alpha() * (1 - ratio) + color2.alpha() * ratio)
    return QColor(r, g, b, a)

class HexViewer(QWidget):
    byte_hovered = Signal(int)
    byte_hovered_leave = Signal()
    byte_clicked = Signal(int)
    data_changed = Signal(memoryview)

    class Colors(Enum):
        NORMAL = 0
        HOVER = 1
        SELECTED = 2
        NULL_VALUE = 3
        CHANGED = 4

    class LineWidth(Enum):
        FIXED = 0
        ANY = 1
        POWER_OF_TWO = 2

    @dataclass
    class _SizeHint:
        width: int
        height: int
        bytes_per_line: int

        @property
        def size(self) -> QSize:
            return QSize(self.width, self.height)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._data = bytearray()
        self._compare_data: bytes | memoryview = b''
        self._config = Config.instance()
        self._padding = 4
        self._current_size_hint: HexViewer._SizeHint = HexViewer._SizeHint(0, 0, 0)
        self._start_address: int = 0
        self._end_address: int = 0
        self._start_hex: int = 0
        self._end_hex: int = 0
        self._start_ascii: int = 0
        self._end_ascii: int = 0
        self._hover_byte: int | None = None
        self._selected_byte: int | None = None
        self._colors: dict[HexViewer.Colors, QColor] = {}
        self._edit_cursor_pos = 0
        self._root_section: ListSection | None = None
        self._encoding = self._config.encoding
        self._byte_char_cache: list[str] = []
        self._byte_char_width_cache: list[int] = []
        self._paint_section_cache: dict[int, list[Section]] | None = None
        self._line_width = self._config.hex_viewer_line_width
        self.setFont(self._config.hex_viewer_font)
        self._rebuild_byte_char_cache()

        self.resize(800, 600)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    @property
    def data(self) -> memoryview:
        '''Get the current data from the hex viewer.'''
        return memoryview(self._data)
    @data.setter
    def data(self, data: bytes | memoryview) -> None:
        '''Set the data to be displayed in the hex viewer.'''
        if self._data == data: # type: ignore (Pylance doesn't understand that memoryview and bytes can be compared)
            return
        if not self._compare_data:
            self._compare_data = data
        self._data = bytearray(data)
        self._set_selected_byte(None)
        self._set_hover_byte(None)
        self._calculate_size()
        self.update()
        self.data_changed.emit(memoryview(self._data))

    @property
    def compare_data(self) -> memoryview:
        '''Get the data to compare against for highlighting changes.'''
        return memoryview(self._compare_data)
    @compare_data.setter
    def compare_data(self, data: bytes | memoryview) -> None:
        '''Set the data to compare against for highlighting changes.'''
        self._compare_data = data
        self.update()
    def set_compare_data(self, data: bytes | memoryview) -> None:
        '''Set the data to compare against for highlighting changes.'''
        self.compare_data = data

    def set_font(self, font: QFont) -> None:
        self.setFont(font)
        self._calculate_size()
        self.update()

    def get_byte_index_at_position(self, pos: QPoint | QPointF, line_start: bool) -> int | None:
        size_hint = self._current_size_hint
        line = int(pos.y()) // self.fontMetrics().height()
        if line < 0 or line >= (len(self._data) + size_hint.bytes_per_line - 1) // size_hint.bytes_per_line:
            return None
        if line_start:
            return line * size_hint.bytes_per_line
        if self._start_hex <= (pos.x() + self._space_width / 2) <= self._end_hex:
            hex_width = self._hex_width * 2 + self._space_width
            column = (int(pos.x() + self._char_width / 2) - self._start_hex) // hex_width
            byte_index = line * size_hint.bytes_per_line + column
            if byte_index < len(self._data):
                return byte_index
        elif self._start_ascii <= pos.x() <= self._end_ascii:
            column = (int(pos.x()) - self._start_ascii) // self._char_width
            byte_index = line * size_hint.bytes_per_line + column
            if byte_index < len(self._data):
                return byte_index
        return None

    def ensure_selected_byte_visible(self) -> None:
        if self._selected_byte is None:
            return
        area = self._get_scroll_area()
        if area is None:
            return
        size_hint = self._current_size_hint
        line = self._selected_byte // size_hint.bytes_per_line
        line_y = line * self.fontMetrics().height()
        if line_y < area.verticalScrollBar().value():
            area.verticalScrollBar().setValue(line_y)
        elif line_y + self.fontMetrics().height() > area.verticalScrollBar().value() + area.viewport().height():
            area.verticalScrollBar().setValue(line_y + self.fontMetrics().height() - area.viewport().height())

    def _get_scroll_area(self) -> QScrollArea | None:
        parent = self.parentWidget()
        while parent is not None:
            if isinstance(parent, QScrollArea):
                return parent
            parent = parent.parentWidget()
        return None

    def set_root_section(self, section: ListSection) -> None:
        self._root_section = section
        self.update()

    def set_encoding(self, encoding: str) -> None:
        self._encoding = encoding
        self._rebuild_byte_char_cache()
        self.update()

    def _rebuild_byte_char_cache(self) -> None:
        cache: list[str] = []
        widths: list[int] = []
        metrics = self.fontMetrics()
        for b in range(256):
            try:
                char = bytes([b]).decode(self._encoding)
            except UnicodeDecodeError:
                char = '�'
            if not char.isprintable():
                char = '☐'
            cache.append(char)
            widths.append(metrics.horizontalAdvance(char))
        self._byte_char_cache = cache
        self._byte_char_width_cache = widths

    def _byte_update_rect(self, byte_idx: int) -> QRect:
        hex_pos = self._get_hex_position(byte_idx)
        ascii_pos = self._get_ascii_position(byte_idx)
        top = hex_pos.y() - self._char_ascent - 1
        height = self._char_height + 2
        hex_rect = QRect(hex_pos.x() - 1, top, self._hex_width * 2 + self._space_width + 2, height)
        ascii_rect = QRect(ascii_pos.x() - 1, top, self._char_width + 2, height)
        return hex_rect.united(ascii_rect)

    def _update_bytes(self, *byte_indices: int | None) -> None:
        rect: QRect | None = None
        for byte_idx in byte_indices:
            if byte_idx is None or byte_idx < 0 or byte_idx >= len(self._data):
                continue
            byte_rect = self._byte_update_rect(byte_idx)
            rect = byte_rect if rect is None else rect.united(byte_rect)
        if rect is None:
            self.update()
        else:
            self.update(rect)

    def _init_colors(self) -> None:
        colors = self._config.hex_viewer_colors
        palette = self.palette()
        defaults: dict[HexViewer.Colors, QColor] = {
            self.Colors.NORMAL: palette.color(QPalette.ColorRole.WindowText),
            self.Colors.HOVER: palette.color(QPalette.ColorRole.Highlight),
            self.Colors.SELECTED: palette.color(QPalette.ColorRole.PlaceholderText),
            self.Colors.NULL_VALUE: palette.color(QPalette.ColorRole.Dark),
            self.Colors.CHANGED: palette.color(QPalette.ColorRole.Link),
        }
        for color in HexViewer.Colors:
            color_name = color.name.lower()
            if color_name in colors and colors[color_name]:
                self._colors[color] = QColor(colors[color_name])
            else:
                self._colors[color] = defaults[color]
        self._config.hex_viewer_colors = {k.name.lower(): v.name() for k, v in self._colors.items()}

    def set_color(self, color: HexViewer.Colors, value: QColor) -> None:
        self._colors[color] = value
        color_config = self._config.hex_viewer_colors
        color_config[color.name.lower()] = value.name()
        self._config.hex_viewer_colors = color_config
        self.update()

    @property
    def line_width(self) -> tuple[HexViewer.LineWidth, int | None]:
        return self._line_width
    @line_width.setter
    def line_width(self, value: HexViewer.LineWidth | int) -> None:
        if isinstance(value, int):
            self._line_width = (HexViewer.LineWidth.FIXED, value)
        else:
            if value == HexViewer.LineWidth.FIXED:
                raise ValueError("LineWidth.FIXED must be set with an integer value.")
            self._line_width = (value, None)
        self.resizeEvent(QResizeEvent(self.size(), self.size()))

    def _calculate_size(self) -> _SizeHint:
        font_metrics = QFontMetrics(self.font())

        def width(length: int) -> int:
            end_ascii = self.calculate_text_positions(length)[5]
            return end_ascii + self._padding

        def find_length(options: list[int], min: int | None, max: int | None) -> int:
            """Recursively find the largest length that fits within the given min and max constraints."""
            if min is None:
                min = 0
            if max is None:
                max = len(options) - 1
            mid = (min + max) // 2
            if min > max:
                return options[max] if max >= 0 else options[0]
            test_length = options[mid]
            if width(test_length) > self.width():
                return find_length(options, min, mid - 1)
            else:
                return find_length(options, mid + 1, max)

        if self._line_width[0] == HexViewer.LineWidth.FIXED:
            count = self._line_width[1] or 16
        else:
            if self._line_width[0] == HexViewer.LineWidth.ANY:
                test_lengths = list(range(1, 1000))
            else:
                test_lengths = [2 ** i for i in range(1, 10)]
            count = find_length(test_lengths, None, None)

        line_height = font_metrics.height()
        lines = (len(self._data) + count - 1) // count
        height = lines * line_height + 2 * self._padding
        self._current_size_hint = self._SizeHint(width(count) + 2 * self._padding, height, count)
        if self._line_width[0] == HexViewer.LineWidth.FIXED:
            self.setMinimumWidth(self._current_size_hint.width)
        else:
            self.setMinimumWidth(0)
        return self._current_size_hint

    def _get_hex_position(self, pos: int) -> QPoint:
        size_hint = self._current_size_hint
        line = pos // size_hint.bytes_per_line
        column = pos % size_hint.bytes_per_line
        x = self._start_hex + column * (self._hex_width * 2 + self._space_width)
        y = line * self.fontMetrics().height() + self._char_ascent + self._padding
        return QPoint(x, y)

    def _get_ascii_position(self, pos: int) -> QPoint:
        size_hint = self._current_size_hint
        line = pos // size_hint.bytes_per_line
        column = pos % size_hint.bytes_per_line
        x = self._start_ascii + column * self._char_width
        y = line * self.fontMetrics().height() + self._char_ascent + self._padding
        return QPoint(x, y)

    def _check_hover_byte(self, point: QPoint | QPointF) -> None:
        byte_idx = self.get_byte_index_at_position(point, False)
        self._set_hover_byte(byte_idx)

    def _update_hover_from_cursor(self) -> None:
        local_pos = self.mapFromGlobal(QCursor.pos())
        self._check_hover_byte(local_pos)

    def _set_selected_byte(self, byte_idx: int | None) -> None:
        if byte_idx != self._selected_byte:
            old_byte = self._selected_byte
            self._selected_byte = byte_idx
            if byte_idx is not None:
                self.byte_clicked.emit(byte_idx)
            self._update_bytes(old_byte, byte_idx)

    def _set_hover_byte(self, byte_idx: int | None) -> None:
        if byte_idx != self._hover_byte:
            old_byte = self._hover_byte
            self._hover_byte = byte_idx
            if byte_idx is not None:
                self.byte_hovered.emit(byte_idx)
            else:
                self.byte_hovered_leave.emit()
            self._update_bytes(old_byte, byte_idx)

    def _sections_for_byte_index(self, byte_idx: int) -> list[Section]:
        if self._root_section is None:
            return []
        return self._root_section.get_sections_for_index(byte_idx)

    def _sections_for_byte_index_cached(self, byte_idx: int) -> list[Section]:
        if self._paint_section_cache is None:
            sections = self._sections_for_byte_index(byte_idx)
            sections.sort(key=lambda s: (s.level, s.absolute_start))
            return sections
        cached = self._paint_section_cache.get(byte_idx)
        if cached is not None:
            return cached
        sections = self._sections_for_byte_index(byte_idx)
        sections.sort(key=lambda s: (s.level, s.absolute_start))
        self._paint_section_cache[byte_idx] = sections
        return sections

    def sizeHint(self) -> QSize:
        return self._current_size_hint.size

    def calculate_text_positions(self, bytes_per_line: int) -> tuple[int, int, int, int, int, int]:
        line_number_width = self._hex_width * 4
        start_address = self._padding
        end_address = start_address + line_number_width
        start_hex = end_address + self._space_width
        hex_byte_width = self._hex_width * 2 + self._space_width
        end_hex = start_hex + hex_byte_width * bytes_per_line
        start_ascii = end_hex
        ascii_byte_width = self._char_width
        end_ascii = start_ascii + ascii_byte_width * bytes_per_line
        return start_address, end_address, start_hex, end_hex, start_ascii, end_ascii

    def resizeEvent(self, event: QResizeEvent) -> None:
        self.setMinimumHeight(self._calculate_size().height)
        self._start_address, self._end_address, self._start_hex, self._end_hex, self._start_ascii, self._end_ascii = self.calculate_text_positions(self._current_size_hint.bytes_per_line)
        super().resizeEvent(event)

    def changeEvent(self, event: QEvent) -> None:
        if event.type() == QEvent.Type.PaletteChange:
            self._init_colors()
        super().changeEvent(event)

    def showEvent(self, event: QShowEvent) -> None:
        self._init_colors()
        super().showEvent(event)

    def setFont(self, font: QFont | str | Sequence[str]) -> None:
        super().setFont(font)
        self._space_width = self.fontMetrics().horizontalAdvance(' ')
        self._char_width = max(self.fontMetrics().horizontalAdvance(chr(c)) for c in range(32, 127))
        self._char_height = self.fontMetrics().height()
        self._char_ascent = self.fontMetrics().ascent()
        self._hex_width = max(self.fontMetrics().horizontalAdvance(c) for c in '0123456789ABCDEF')
        self.resizeEvent(QResizeEvent(self.size(), self.size()))

    @dataclass
    class _PaintInfo:
        outer: HexViewer
        line_data: memoryview
        painter: QPainter
        line: int
        col: int

        @cached_property
        def byte_index(self) -> int:
            return self.line * self.outer._current_size_hint.bytes_per_line + self.col

        @cached_property
        def hex_pos(self) -> QPoint:
            return self.outer._get_hex_position(self.byte_index)

        @cached_property
        def ascii_pos(self) -> QPoint:
            return self.outer._get_ascii_position(self.byte_index)

        @cached_property
        def sections(self) -> list[Section]:
            return self.outer._sections_for_byte_index_cached(self.byte_index)
        @property
        def top_section(self) -> Section | None:
            return self.sections[-1] if self.sections else None

        @property
        def last_column(self) -> bool:
            return self.col == len(self.line_data) - 1

        def same_left(self, level: int = -1) -> bool:
            if self.col == 0 or self.top_section is None:
                return False
            return self.sections[level].contains_absolute_index(self.byte_index - 1)

        def same_right(self, level: int = -1) -> bool:
            if self.last_column or self.top_section is None:
                return False
            return self.sections[level].contains_absolute_index(self.byte_index + 1)

        def same_up(self, level: int = -1) -> bool:
            if self.top_section is None:
                return False
            size_hint = self.outer._current_size_hint
            return self.sections[level].contains_absolute_index(self.byte_index - size_hint.bytes_per_line)

        def same_down(self, level: int = -1) -> bool:
            if self.top_section is None:
                return False
            size_hint = self.outer._current_size_hint
            return self.sections[level].contains_absolute_index(self.byte_index + size_hint.bytes_per_line)


    def paintEvent(self, event: QPaintEvent) -> None:
        '''Paint the hex viewer.'''
        painter = QPainter(self)
        painter.setFont(self.font())
        data = memoryview(self._data)
        self._paint_section_cache = {}

        range_start = self.get_byte_index_at_position(event.rect().topLeft(), True) or 0
        range_start = max(range_start - self._current_size_hint.bytes_per_line, 0)
        range_end = self.get_byte_index_at_position(event.rect().bottomRight(), True) or len(data)
        range_end = min(range_end + self._current_size_hint.bytes_per_line, len(data))

        size_hint = self._current_size_hint
        for line in range(range_start, range_end, size_hint.bytes_per_line):
            painter.setPen(self.palette().color(QPalette.ColorRole.WindowText))
            y = (line // size_hint.bytes_per_line) * painter.fontMetrics().height() + \
                self._char_ascent + self._padding
            line_data = data[line:line+size_hint.bytes_per_line]
            start_text = f'{line:04X} '
            painter.drawText(self._padding, y, start_text)

            for i in range(len(line_data)):
                info = self._PaintInfo(self, line_data, painter, line // size_hint.bytes_per_line, i)
                self.paint_background(info)

            for i in range(len(line_data)):
                info = self._PaintInfo(self, line_data, painter, line // size_hint.bytes_per_line, i)
                self.paint_border(info)
                self.paint_text(info)

            painter.setPen(self.palette().color(QPalette.ColorRole.WindowText))
        self._paint_section_cache = None
        painter.end()

    def paint_background(self, info: _PaintInfo) -> None:
        for level, section in enumerate(info.sections):
            color = section.color
            if color:
                back_color = _blend_color(color, self.palette().color(QPalette.ColorRole.Window), 0.8)
                info.painter.setBrush(back_color)
                d = self._char_width - 1 if info.same_right(level) else 0
                info.painter.fillRect(info.hex_pos.x(), info.hex_pos.y() - self._char_ascent,
                                      self._hex_width * 2 + d, self._char_height, back_color)
                info.painter.fillRect(info.ascii_pos.x(), info.ascii_pos.y() - self._char_ascent,
                                    self._char_width, self._char_height, back_color)

    def paint_border(self, info: _PaintInfo) -> None:
        for level, section in enumerate(info.sections):
            color = section.color
            if color:
                info.painter.setPen(color)
                width = self._hex_width * 2
                if not info.last_column and info.same_right(level):
                    width += self._space_width
                if not info.same_left(level):
                    info.painter.drawLine(info.hex_pos.x(), info.hex_pos.y() - self._char_ascent,
                                          info.hex_pos.x(), info.hex_pos.y() - self._char_ascent + self._char_height - 1)
                    info.painter.drawLine(info.ascii_pos.x(), info.ascii_pos.y() - self._char_ascent,
                                          info.ascii_pos.x(), info.ascii_pos.y() - self._char_ascent + self._char_height - 1)
                if not info.same_up(level):
                    info.painter.drawLine(info.hex_pos.x(), info.hex_pos.y() - self._char_ascent,
                                          info.hex_pos.x() + width, info.hex_pos.y() - self._char_ascent)
                    info.painter.drawLine(info.ascii_pos.x(), info.ascii_pos.y() - self._char_ascent,
                                          info.ascii_pos.x() + self._char_width, info.ascii_pos.y() - self._char_ascent)
                if not info.same_right(level):
                    info.painter.drawLine(info.hex_pos.x() + width, info.hex_pos.y() - self._char_ascent,
                                          info.hex_pos.x() + width, info.hex_pos.y() - self._char_ascent + self._char_height - 1)
                    info.painter.drawLine(info.ascii_pos.x() + self._char_width, info.ascii_pos.y() - self._char_ascent,
                                          info.ascii_pos.x() + self._char_width, info.ascii_pos.y() - self._char_ascent + self._char_height - 1)
                if not info.same_down(level):
                    down_left = self._sections_for_byte_index_cached(info.byte_index + self._current_size_hint.bytes_per_line - 1)
                    same_down_left = info.same_left(level) and section in down_left
                    d = self._space_width - 1 if info.same_left(level) and same_down_left else 0
                    info.painter.drawLine(info.hex_pos.x() - d, info.hex_pos.y() - self._char_ascent + self._char_height - 1,
                                          info.hex_pos.x() + width + d, info.hex_pos.y() - self._char_ascent + self._char_height - 1)
                    info.painter.drawLine(info.ascii_pos.x(), info.ascii_pos.y() - self._char_ascent + self._char_height - 1,
                                          info.ascii_pos.x() + self._char_width, info.ascii_pos.y() - self._char_ascent + self._char_height - 1)

    def paint_text(self, info: _PaintInfo) -> None:
        b = info.line_data[info.col]
        if b == 0:
            text_color = self._colors[self.Colors.NULL_VALUE]
        else:
            text_color = self._colors[self.Colors.NORMAL]
        hovered = info.byte_index == self._hover_byte
        selected = info.byte_index == self._selected_byte
        if hovered and selected:
            text_color = _blend_color(self._colors[self.Colors.HOVER], self._colors[self.Colors.SELECTED])
        elif hovered:
            text_color = self._colors[self.Colors.HOVER]
        elif selected:
            text_color = self._colors[self.Colors.SELECTED]

        if len(self._compare_data) > info.byte_index and self._compare_data[info.byte_index] != b:
            text_color = _blend_color(text_color, self._colors[self.Colors.CHANGED], 0.7)

        info.painter.setPen(text_color)
        info.painter.drawText(info.hex_pos, f'{b:02X}')

        if selected and self.hasFocus():
            cursor_x = info.hex_pos.x() + (self._char_width if self._edit_cursor_pos == 1 else 0)
            cursor_y = info.hex_pos.y() - self._char_ascent
            info.painter.drawLine(cursor_x, cursor_y, cursor_x, cursor_y + self._char_height)

        char = self._byte_char_cache[b]
        char_width = self._byte_char_width_cache[b]
        char_x = info.ascii_pos.x() + (self._char_width - char_width) // 2
        info.painter.drawText(QPoint(char_x, info.ascii_pos.y()), char)


    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        self._check_hover_byte(event.position())
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        byte_idx = self.get_byte_index_at_position(event.position(), False)
        self._set_selected_byte(byte_idx)
        super().mousePressEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        if self._hover_byte is not None:
            self._set_hover_byte(None)
        super().leaveEvent(event)

    def wheelEvent(self, event: QWheelEvent) -> None:
        super().wheelEvent(event)
        QTimer.singleShot(0, self._update_hover_from_cursor)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in HEX_EDIT_KEYS:
            if self._selected_byte is not None:
                byte_value = self._data[self._selected_byte]
                if event.key() in NUMBER_KEYS:
                    digit = event.key() - Qt.Key.Key_0
                elif event.key() in LETTER_KEYS:
                    digit = event.key() - Qt.Key.Key_A + 10
                else:
                    super().keyPressEvent(event)
                    return
                if self._edit_cursor_pos == 0:
                    new_value = (byte_value & 0x0F) | (digit << 4)
                else:
                    new_value = (byte_value & 0xF0) | digit
                if new_value != byte_value:
                    self._data[self._selected_byte] = new_value
                    self.data_changed.emit(memoryview(self._data))

                if self._edit_cursor_pos == 0:
                    self._edit_cursor_pos = 1
                    previous_byte = self._selected_byte
                else:
                    self._edit_cursor_pos = 0
                    previous_byte = self._selected_byte
                    if self._selected_byte + 1 < len(self._data):
                        self._selected_byte += 1

                self.byte_clicked.emit(self._selected_byte)
                self._update_bytes(previous_byte, self._selected_byte)

        elif event.key() == Qt.Key.Key_Escape:
            self._set_selected_byte(None)
        elif event.key() == Qt.Key.Key_Left:
            if self._selected_byte is not None:
                if self._edit_cursor_pos == 1:
                    self._edit_cursor_pos = 0
                    self._update_bytes(self._selected_byte)
                elif self._selected_byte > 0:
                    self._edit_cursor_pos = 1
                    self._set_selected_byte(self._selected_byte - 1)
            else:
                self._set_selected_byte(len(self._data) - 1)
        elif event.key() == Qt.Key.Key_Right:
            if self._selected_byte is not None:
                if self._edit_cursor_pos == 0:
                    self._edit_cursor_pos = 1
                    self._update_bytes(self._selected_byte)
                elif self._selected_byte + 1 < len(self._data):
                    self._edit_cursor_pos = 0
                    self._set_selected_byte(self._selected_byte + 1)
            else:
                self._set_selected_byte(0)
        elif event.key() == Qt.Key.Key_Up:
            if self._selected_byte is not None:
                size_hint = self._current_size_hint
                if self._selected_byte >= size_hint.bytes_per_line:
                    self._set_selected_byte(self._selected_byte - size_hint.bytes_per_line)
            else:
                self._set_selected_byte(0)
        elif event.key() == Qt.Key.Key_Down:
            if self._selected_byte is not None:
                size_hint = self._current_size_hint
                if self._selected_byte + size_hint.bytes_per_line < len(self._data):
                    self._set_selected_byte(self._selected_byte + size_hint.bytes_per_line)
            else:
                self._set_selected_byte(0)
        elif event.key() == Qt.Key.Key_Home:
            if self._selected_byte is not None:
                size_hint = self._current_size_hint
                line_start = (self._selected_byte // size_hint.bytes_per_line) * size_hint.bytes_per_line
                self._set_selected_byte(line_start)
            else:
                self._set_selected_byte(0)
        elif event.key() == Qt.Key.Key_End:
            if self._selected_byte is not None:
                size_hint = self._current_size_hint
                line_start = (self._selected_byte // size_hint.bytes_per_line) * size_hint.bytes_per_line
                line_end = min(line_start + size_hint.bytes_per_line - 1, len(self._data) - 1)
                self._set_selected_byte(line_end)
            else:
                self._set_selected_byte(len(self._data) - 1)
        elif event.key() == Qt.Key.Key_PageUp:
            if self._selected_byte is not None:
                scroll_area = self._get_scroll_area()
                if scroll_area is None:
                    height = self.height()
                else:
                    height = scroll_area.viewport().height()
                size_hint = self._current_size_hint
                bytes_per_page = size_hint.bytes_per_line * (height // self.fontMetrics().height())
                new_selected = self._selected_byte - bytes_per_page
                if new_selected < 0:
                    new_selected = 0
                    self._edit_cursor_pos = 0
                self._set_selected_byte(new_selected)
            else:
                self._set_selected_byte(0)
        elif event.key() == Qt.Key.Key_PageDown:
            if self._selected_byte is not None:
                scroll_area = self._get_scroll_area()
                if scroll_area is None:
                    height = self.height()
                else:
                    height = scroll_area.viewport().height()
                size_hint = self._current_size_hint
                bytes_per_page = size_hint.bytes_per_line * (height // self.fontMetrics().height())
                new_selected = self._selected_byte + bytes_per_page
                self._set_selected_byte(min(new_selected, len(self._data) - 1))
            else:
                self._set_selected_byte(0)
        else:
            super().keyPressEvent(event)
            return

        self.ensure_selected_byte_visible()

