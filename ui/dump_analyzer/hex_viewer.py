''' Widget for displaying binary data in a hex viewer format. '''

from dataclasses import dataclass
from enum import Enum

from PySide6.QtCore import QEvent, QPoint, QPointF, QSize, QTimer, Signal
from PySide6.QtGui import (QColor, QCursor, QFont, QFontMetrics, QMouseEvent,
                           QPainter, QPaintEvent, QPalette, QResizeEvent,
                           QShowEvent, QWheelEvent)
from PySide6.QtWidgets import QWidget

from ui.config import Config

class HexViewer(QWidget):
    byte_hovered = Signal(int)
    byte_hovered_leave = Signal()
    byte_clicked = Signal(int)

    class Colors(Enum):
        NORMAL = 0
        HOVER = 1
        SELECTED = 2
        NULL_VALUE = 3

    @dataclass
    class SizeHint:
        width: int
        height: int
        bytes_per_line: int

        @property
        def size(self) -> QSize:
            return QSize(self.width, self.height)

    def __init__(self, data: bytes, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._config = Config.instance()
        self._data: bytes = data
        self._padding = 4
        self._current_size_hint: HexViewer.SizeHint = HexViewer.SizeHint(0, 0, 0)
        self._start_address: int = 0
        self._end_address: int = 0
        self._start_hex: int = 0
        self._end_hex: int = 0
        self._start_ascii: int = 0
        self._end_ascii: int = 0
        self._hover_byte: int | None = None
        self._selected_byte: int | None = None
        self._colors: dict[HexViewer.Colors, QColor] = {}

        self.resize(800, 600)
        font = self.font()
        font.setPointSize(10)
        font.setFamily("Courier")
        self.setFont(font)
        self.setMouseTracking(True)

    def set_data(self, data: bytes) -> None:
        '''Set the data to be displayed in the hex viewer.'''
        self._data = data
        self._set_selected_byte(None)
        self._set_hover_byte(None)
        self._calculate_size()
        self.repaint()

    def set_font(self, font: QFont) -> None:
        self.setFont(font)
        self._calculate_size()
        self.repaint()

    def get_byte_index_at_position(self, pos: QPoint | QPointF, line_start: bool) -> int | None:
        size_hint = self._current_size_hint
        line = int(pos.y()) // self.fontMetrics().height()
        if line < 0 or line >= (len(self._data) + size_hint.bytes_per_line - 1) // size_hint.bytes_per_line:
            return None
        if line_start:
            return line * size_hint.bytes_per_line
        ascii_width = self.fontMetrics().horizontalAdvance(' ')
        if self._start_hex <= (pos.x() + ascii_width / 2) <= self._end_hex:
            hex_width = self.fontMetrics().horizontalAdvance('00 ')
            column = (int(pos.x() + ascii_width / 2) - self._start_hex) // hex_width
            byte_index = line * size_hint.bytes_per_line + column
            if byte_index < len(self._data):
                return byte_index
        elif self._start_ascii <= pos.x() <= self._end_ascii:
            column = (int(pos.x()) - self._start_ascii) // ascii_width
            byte_index = line * size_hint.bytes_per_line + column
            if byte_index < len(self._data):
                return byte_index
        return None

    def _init_colors(self) -> None:
        colors = self._config.hex_viewer_colors
        if colors:
            self._colors[self.Colors.NORMAL] = QColor(colors.get("normal", "#000000"))
            self._colors[self.Colors.HOVER] = QColor(colors.get("hover", "#0000FF"))
            self._colors[self.Colors.SELECTED] = QColor(colors.get("selected", "#FF0000"))
            self._colors[self.Colors.NULL_VALUE] = QColor(colors.get("null_value", "#888888"))
        else:
            palette = self.palette()
            self._colors[HexViewer.Colors.NORMAL] = palette.color(QPalette.ColorRole.WindowText)
            self._colors[HexViewer.Colors.HOVER] = palette.color(QPalette.ColorRole.Highlight)
            self._colors[HexViewer.Colors.SELECTED] = palette.color(QPalette.ColorRole.PlaceholderText)
            self._colors[HexViewer.Colors.NULL_VALUE] = palette.color(QPalette.ColorRole.Dark)
            self._config.hex_viewer_colors = {k.name.lower(): v.name() for k, v in self._colors.items()}

    def _calculate_size(self) -> SizeHint:
        font_metrics = QFontMetrics(self.font())
        test_sizes: list[tuple[int, int]] = []
        for e in range(1, 10):
            elements = 2 ** e
            test_string = '0000: '
            for _ in range(elements):
                test_string += '00 '
            test_string += ' '
            test_string += ' ' * elements
            size = font_metrics.size(0, test_string)
            test_sizes.append((elements, size.width()))

        count = 1
        last_width = 0
        for count, width in test_sizes:
            if width > self.width():
                break
            last_width = width
        count //= 2

        line_height = font_metrics.height()
        lines = (len(self._data) + count - 1) // count
        height = lines * line_height + 2 * self._padding
        self._current_size_hint = self.SizeHint(last_width + 2 * self._padding, height, count)
        return self._current_size_hint

    def _get_hex_position(self, pos: int) -> QPoint:
        size_hint = self._current_size_hint
        line = pos // size_hint.bytes_per_line
        column = pos % size_hint.bytes_per_line
        x = self._start_hex + column * self.fontMetrics().horizontalAdvance('00 ')
        y = line * self.fontMetrics().height() + self.fontMetrics().ascent() + self._padding
        return QPoint(x, y)

    def _get_ascii_position(self, pos: int) -> QPoint:
        size_hint = self._current_size_hint
        line = pos // size_hint.bytes_per_line
        column = pos % size_hint.bytes_per_line
        x = self._start_ascii + column * self.fontMetrics().horizontalAdvance(' ')
        y = line * self.fontMetrics().height() + self.fontMetrics().ascent() + self._padding
        return QPoint(x, y)

    def _check_hover_byte(self, point: QPoint | QPointF) -> None:
        byte_idx = self.get_byte_index_at_position(point, False)
        self._set_hover_byte(byte_idx)

    def _update_hover_from_cursor(self) -> None:
        local_pos = self.mapFromGlobal(QCursor.pos())
        self._check_hover_byte(local_pos)

    def _set_selected_byte(self, byte_idx: int | None) -> None:
        if byte_idx != self._selected_byte:
            self._selected_byte = byte_idx
            if byte_idx is not None:
                self.byte_clicked.emit(byte_idx)
            self.repaint()

    def _set_hover_byte(self, byte_idx: int | None) -> None:
        if byte_idx != self._hover_byte:
            self._hover_byte = byte_idx
            if byte_idx is not None:
                self.byte_hovered.emit(byte_idx)
            else:
                self.byte_hovered_leave.emit()
            self.repaint()

    def sizeHint(self) -> QSize:
        return self._current_size_hint.size

    def resizeEvent(self, event: QResizeEvent) -> None:
        self.setMinimumHeight(self._calculate_size().height)
        font_metrics = QFontMetrics(self.font())
        line_number_width = font_metrics.horizontalAdvance('0000:')
        self._start_address = self._padding
        self._end_address = self._start_address + line_number_width
        space_width = font_metrics.horizontalAdvance(' ')
        self._start_hex = self._end_address + space_width
        hex_byte_width = font_metrics.horizontalAdvance('00 ')
        self._end_hex = self._start_hex + hex_byte_width * self._current_size_hint.bytes_per_line
        self._start_ascii = self._end_hex + space_width
        ascii_byte_width = font_metrics.horizontalAdvance('X')
        self._end_ascii = self._start_ascii + \
                          ascii_byte_width * self._current_size_hint.bytes_per_line
        super().resizeEvent(event)

    def changeEvent(self, event: QEvent) -> None:
        if event.type() == QEvent.Type.PaletteChange:
            self._init_colors()
        super().changeEvent(event)

    def showEvent(self, event: QShowEvent) -> None:
        self._init_colors()
        super().showEvent(event)

    def paintEvent(self, event: QPaintEvent) -> None:
        '''Paint the hex viewer.'''
        painter = QPainter(self)
        painter.setFont(self.font())

        range_start = self.get_byte_index_at_position(event.rect().topLeft(), True) or 0
        range_start = max(range_start - self._current_size_hint.bytes_per_line, 0)
        range_end = self.get_byte_index_at_position(event.rect().bottomRight(), True) or len(self._data)
        range_end = min(range_end + self._current_size_hint.bytes_per_line, len(self._data))

        size_hint = self._calculate_size()
        for line in range(range_start, range_end, size_hint.bytes_per_line):
            y = (line // size_hint.bytes_per_line) * painter.fontMetrics().height() + \
                painter.fontMetrics().ascent() + self._padding
            line_data = self._data[line:line+size_hint.bytes_per_line]
            start_text = f'{line:04X}: '
            painter.drawText(self._padding, y, start_text)

            for i, b in enumerate(line_data):
                byte_idx = line + i
                color = self._colors[self.Colors.NORMAL]
                if byte_idx == self._hover_byte:
                    color = self._colors[self.Colors.HOVER]
                elif byte_idx == self._selected_byte:
                    color = self._colors[self.Colors.SELECTED]
                elif b == 0:
                    color = self._colors[self.Colors.NULL_VALUE]
                painter.setPen(color)
                pos = self._get_hex_position(byte_idx)
                painter.drawText(pos, f'{b:02X}')
                pos = self._get_ascii_position(byte_idx)
                char = chr(b) if 32 <= b < 127 else '.'
                painter.drawText(pos, char)
            painter.setPen(self._colors[self.Colors.NORMAL])

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
