''' Widget for displaying binary data in a hex viewer format. '''

from dataclasses import dataclass
from enum import Enum

from PySide6.QtCore import QEvent, QPoint, QPointF, QSize, QTimer, Signal
from PySide6.QtGui import (QColor, QCursor, QFont, QFontMetrics, QKeyEvent,
                           QMouseEvent, QPainter, QPaintEvent, QPalette,
                           QResizeEvent, QShowEvent, Qt, QWheelEvent)
from PySide6.QtWidgets import QScrollArea, QWidget

from ui.config import Config

NUMBER_KEYS = set(range(Qt.Key.Key_0, Qt.Key.Key_9 + 1))
LETTER_KEYS = set(range(Qt.Key.Key_A, Qt.Key.Key_F + 1))
HEX_EDIT_KEYS = NUMBER_KEYS.union(LETTER_KEYS)

def _blend_color(color1: QColor, color2: QColor, ratio: float = 0.5) -> QColor:
    r = int(color1.red() * (1 - ratio) + color2.red() * ratio)
    g = int(color1.green() * (1 - ratio) + color2.green() * ratio)
    b = int(color1.blue() * (1 - ratio) + color2.blue() * ratio)
    return QColor(r, g, b)

class HexViewer(QWidget):
    byte_hovered = Signal(int)
    byte_hovered_leave = Signal()
    byte_clicked = Signal(int)

    class Colors(Enum):
        NORMAL = 0
        HOVER = 1
        SELECTED = 2
        NULL_VALUE = 3
        CHANGED = 4

    @dataclass
    class SizeHint:
        width: int
        height: int
        bytes_per_line: int

        @property
        def size(self) -> QSize:
            return QSize(self.width, self.height)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._data = bytearray()
        self._config = Config.instance()
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
        self._edit_cursor_pos = 0

        self.resize(800, 600)
        font = self.font()
        font.setPointSize(10)
        font.setFamily("Courier")
        self.setFont(font)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    @property
    def data(self) -> memoryview:
        '''Get the current data from the hex viewer.'''
        return memoryview(self._data)
    @data.setter
    def data(self, data: bytes) -> None:
        '''Set the data to be displayed in the hex viewer.'''
        self._data_source = data
        self._data = bytearray(data)
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

    def _init_colors(self) -> None:
        colors = self._config.hex_viewer_colors
        if colors:
            self._colors[self.Colors.NORMAL] = QColor(colors.get("normal", "#000000"))
            self._colors[self.Colors.HOVER] = QColor(colors.get("hover", "#0000FF"))
            self._colors[self.Colors.SELECTED] = QColor(colors.get("selected", "#FFFF00"))
            self._colors[self.Colors.NULL_VALUE] = QColor(colors.get("null_value", "#888888"))
            self._colors[self.Colors.CHANGED] = QColor(colors.get("changed", "#FF0000"))
        else:
            palette = self.palette()
            self._colors[HexViewer.Colors.NORMAL] = palette.color(QPalette.ColorRole.WindowText)
            self._colors[HexViewer.Colors.HOVER] = palette.color(QPalette.ColorRole.Highlight)
            self._colors[HexViewer.Colors.SELECTED] = palette.color(QPalette.ColorRole.PlaceholderText)
            self._colors[HexViewer.Colors.NULL_VALUE] = palette.color(QPalette.ColorRole.Dark)
            self._colors[HexViewer.Colors.CHANGED] = palette.color(QPalette.ColorRole.Link)
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
                if b == 0:
                    color = self._colors[self.Colors.NULL_VALUE]
                else:
                    color = self._colors[self.Colors.NORMAL]
                hovered = byte_idx == self._hover_byte
                selected = byte_idx == self._selected_byte
                if hovered and selected:
                    color = _blend_color(self._colors[self.Colors.HOVER], self._colors[self.Colors.SELECTED])
                elif hovered:
                    color = self._colors[self.Colors.HOVER]
                elif selected:
                    color = self._colors[self.Colors.SELECTED]

                if self._data_source[byte_idx] != b:
                    color = _blend_color(color, self._colors[self.Colors.CHANGED], 0.7)

                painter.setPen(color)
                pos = self._get_hex_position(byte_idx)
                painter.drawText(pos, f'{b:02X}')

                if selected and self.hasFocus():
                    cursor_x = pos.x() + (self.fontMetrics().horizontalAdvance('0') if self._edit_cursor_pos == 1 else 0)
                    cursor_y = pos.y() - self.fontMetrics().ascent()
                    painter.drawLine(cursor_x, cursor_y, cursor_x, cursor_y + self.fontMetrics().height())

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
                self._data[self._selected_byte] = new_value

                if self._edit_cursor_pos == 0:
                    self._edit_cursor_pos = 1
                else:
                    self._edit_cursor_pos = 0
                    if self._selected_byte + 1 < len(self._data):
                        self._selected_byte += 1

                self.byte_clicked.emit(self._selected_byte)
                self.repaint()

        elif event.key() == Qt.Key.Key_Escape:
            self._set_selected_byte(None)
        elif event.key() == Qt.Key.Key_Left:
            if self._selected_byte is not None:
                if self._edit_cursor_pos == 1:
                    self._edit_cursor_pos = 0
                    self.repaint()
                elif self._selected_byte > 0:
                    self._edit_cursor_pos = 1
                    self._set_selected_byte(self._selected_byte - 1)
            else:
                self._set_selected_byte(len(self._data) - 1)
        elif event.key() == Qt.Key.Key_Right:
            if self._selected_byte is not None:
                if self._edit_cursor_pos == 0:
                    self._edit_cursor_pos = 1
                    self.repaint()
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

