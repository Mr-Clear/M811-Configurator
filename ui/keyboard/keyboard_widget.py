"""A self-contained PySide6 keyboard-layout renderer.

Run this file directly to open the demo application:
    python ui/keyboard_image.py
"""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QEvent, QPointF, QRectF, Qt
from PySide6.QtGui import (QColor, QFont, QMouseEvent, QPainter, QPainterPath,
                           QPaintEvent, QPen)
from PySide6.QtWidgets import QWidget

from .layouts import KeyboardLayout, Modifier, known_layouts
from .physical_layout import PhysicalLayout
from .usb_hid import ScanCode


@dataclass(frozen=True)
class KeyPosition:
    x: float
    y: float
    width: float = 1.0
    height: float = 1.0
    special_shape: bool = False


# The coordinates use key units.  Every declaration begins with its USB HID
# keyboard usage (scan) code.  Empty columns separate the keyboard clusters.
key_positions_ansi: dict[ScanCode, KeyPosition] = {
    ScanCode.ESC: KeyPosition(0, 0),
    ScanCode.F1: KeyPosition(1.5, 0),
    ScanCode.F2: KeyPosition(2.5, 0),
    ScanCode.F3: KeyPosition(3.5, 0),
    ScanCode.F4: KeyPosition(4.5, 0),
    ScanCode.F5: KeyPosition(6, 0),
    ScanCode.F6: KeyPosition(7, 0),
    ScanCode.F7: KeyPosition(8, 0),
    ScanCode.F8: KeyPosition(9, 0),
    ScanCode.F9: KeyPosition(10.5, 0),
    ScanCode.F10: KeyPosition(11.5, 0),
    ScanCode.F11: KeyPosition(12.5, 0),
    ScanCode.F12: KeyPosition(13.5, 0),
    ScanCode.PRINT: KeyPosition(15.25, 0),
    ScanCode.SCROLLLOCK: KeyPosition(16.25, 0),
    ScanCode.PAUSE: KeyPosition(17.25, 0),
    ScanCode.GRAVE: KeyPosition(0, 1.25),
    ScanCode.ONE: KeyPosition(1, 1.25),
    ScanCode.TWO: KeyPosition(2, 1.25),
    ScanCode.THREE: KeyPosition(3, 1.25),
    ScanCode.FOUR: KeyPosition(4, 1.25),
    ScanCode.FIVE: KeyPosition(5, 1.25),
    ScanCode.SIX: KeyPosition(6, 1.25),
    ScanCode.SEVEN: KeyPosition(7, 1.25),
    ScanCode.EIGHT: KeyPosition(8, 1.25),
    ScanCode.NINE: KeyPosition(9, 1.25),
    ScanCode.ZERO: KeyPosition(10, 1.25),
    ScanCode.MINUS: KeyPosition(11, 1.25),
    ScanCode.EQUAL: KeyPosition(12, 1.25),
    ScanCode.BACKSPACE: KeyPosition(13, 1.25, width=2),
    ScanCode.INSERT: KeyPosition(15.25, 1.25),
    ScanCode.HOME: KeyPosition(16.25, 1.25),
    ScanCode.PAGEUP: KeyPosition(17.25, 1.25),
    ScanCode.NUMLOCK: KeyPosition(18.5, 1.25),
    ScanCode.KPSLASH: KeyPosition(19.5, 1.25),
    ScanCode.KPASTERISK: KeyPosition(20.5, 1.25),
    ScanCode.KPMINUS: KeyPosition(21.5, 1.25),
    ScanCode.TAB: KeyPosition(0, 2.25, width=1.5),
    ScanCode.Q: KeyPosition(1.5, 2.25),
    ScanCode.W: KeyPosition(2.5, 2.25),
    ScanCode.E: KeyPosition(3.5, 2.25),
    ScanCode.R: KeyPosition(4.5, 2.25),
    ScanCode.T: KeyPosition(5.5, 2.25),
    ScanCode.Y: KeyPosition(6.5, 2.25),
    ScanCode.U: KeyPosition(7.5, 2.25),
    ScanCode.I: KeyPosition(8.5, 2.25),
    ScanCode.O: KeyPosition(9.5, 2.25),
    ScanCode.P: KeyPosition(10.5, 2.25),
    ScanCode.LEFTBRACE: KeyPosition(11.5, 2.25),
    ScanCode.RIGHTBRACE: KeyPosition(12.5, 2.25),
    ScanCode.BACKSLASH_ANSI: KeyPosition(13.5, 2.25, width=1.5),
    ScanCode.DELETE: KeyPosition(15.25, 2.25),
    ScanCode.END: KeyPosition(16.25, 2.25),
    ScanCode.PAGEDOWN: KeyPosition(17.25, 2.25),
    ScanCode.KP7: KeyPosition(18.5, 2.25),
    ScanCode.KP8: KeyPosition(19.5, 2.25),
    ScanCode.KP9: KeyPosition(20.5, 2.25),
    ScanCode.KPPLUS: KeyPosition(21.5, 2.25, height=2),
    ScanCode.CAPSLOCK: KeyPosition(0, 3.25, width=1.8),
    ScanCode.A: KeyPosition(1.8, 3.25),
    ScanCode.S: KeyPosition(2.8, 3.25),
    ScanCode.D: KeyPosition(3.8, 3.25),
    ScanCode.F: KeyPosition(4.8, 3.25),
    ScanCode.G: KeyPosition(5.8, 3.25),
    ScanCode.H: KeyPosition(6.8, 3.25),
    ScanCode.J: KeyPosition(7.8, 3.25),
    ScanCode.K: KeyPosition(8.8, 3.25),
    ScanCode.L: KeyPosition(9.8, 3.25),
    ScanCode.SEMICOLON: KeyPosition(10.8, 3.25),
    ScanCode.APOSTROPHE: KeyPosition(11.8, 3.25),
    ScanCode.ENTER: KeyPosition(12.8, 3.25, width=2.2),
    ScanCode.KP4: KeyPosition(18.5, 3.25),
    ScanCode.KP5: KeyPosition(19.5, 3.25),
    ScanCode.KP6: KeyPosition(20.5, 3.25),
    ScanCode.LEFTSHIFT: KeyPosition(0, 4.25, width=2.3),
    ScanCode.Z: KeyPosition(2.3, 4.25),
    ScanCode.X: KeyPosition(3.3, 4.25),
    ScanCode.C: KeyPosition(4.3, 4.25),
    ScanCode.V: KeyPosition(5.3, 4.25),
    ScanCode.B: KeyPosition(6.3, 4.25),
    ScanCode.N: KeyPosition(7.3, 4.25),
    ScanCode.M: KeyPosition(8.3, 4.25),
    ScanCode.COMMA: KeyPosition(9.3, 4.25),
    ScanCode.DOT: KeyPosition(10.3, 4.25),
    ScanCode.SLASH: KeyPosition(11.3, 4.25),
    ScanCode.RIGHTSHIFT: KeyPosition(12.3, 4.25, width=2.7),
    ScanCode.UP: KeyPosition(16.25, 4.25),
    ScanCode.KP1: KeyPosition(18.5, 4.25),
    ScanCode.KP2: KeyPosition(19.5, 4.25),
    ScanCode.KP3: KeyPosition(20.5, 4.25),
    ScanCode.KPENTER: KeyPosition(21.5, 4.25, height=2),
    ScanCode.LEFTCTRL: KeyPosition(0, 5.25, width=1.35),
    ScanCode.LEFTMETA: KeyPosition(1.35, 5.25, width=1.25),
    ScanCode.LEFTALT: KeyPosition(2.6, 5.25, width=1.25),
    ScanCode.SPACE: KeyPosition(3.85, 5.25, width=6.3),
    ScanCode.RIGHTALT: KeyPosition(10.15, 5.25, width=1.25),
    ScanCode.RIGHTMETA: KeyPosition(11.4, 5.25, width=1.1),
    ScanCode.PROPS: KeyPosition(12.5, 5.25, width=1.2),
    ScanCode.RIGHTCTRL: KeyPosition(13.7, 5.25, width=1.3),
    ScanCode.LEFT: KeyPosition(15.25, 5.25),
    ScanCode.DOWN: KeyPosition(16.25, 5.25),
    ScanCode.RIGHT: KeyPosition(17.25, 5.25),
    ScanCode.KP0: KeyPosition(18.5, 5.25, width=2),
    ScanCode.KPDOT: KeyPosition(20.5, 5.25),
}

key_positions_iso = key_positions_ansi.copy()
key_positions_iso.pop(ScanCode.BACKSLASH_ANSI)
key_positions_iso[ScanCode.LEFTSHIFT] = KeyPosition(0, 4.25, width=1.3)
key_positions_iso[ScanCode.BACKSLASH_ISO] = KeyPosition(1.3, 4.25)
key_positions_iso[ScanCode.HASHTILDE_ISO] = KeyPosition(12.8, 3.25)
key_positions_iso[ScanCode.ENTER] = KeyPosition(13.5, 2.25, width=1.5, height=2, special_shape=True)


physical_layouts = {
    PhysicalLayout.ANSI: key_positions_ansi,
    PhysicalLayout.ISO: key_positions_iso,
}


@dataclass
class KeyLabels:
    """The labels to display on a physical key."""
    primary: str | None
    top_left: str | None = None
    top_right: str | None = None
    bottom_left: str | None = None
    bottom_right: str | None = None

class KeyboardWidget(QWidget):
    """Paints a responsive keyboard and highlights the last clicked key."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(980, 460)
        self.setMouseTracking(True)
        self._hovered: KeyPosition | None = None
        self._selected: KeyPosition | None = None
        self._key_rects: list[tuple[KeyPosition, QRectF]] = []
        self._layout = list(known_layouts().values())[0]

    def _key_at(self, point: QPointF) -> KeyPosition | None:
        for key, rect in self._key_rects:
            if rect.contains(point):
                return key
        return None

    def set_layout(self, layout: KeyboardLayout) -> None:
        self._layout = layout
        self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # type: ignore[override]
        key = self._key_at(event.position())
        if key != self._hovered:
            self._hovered = key
            self.setCursor(Qt.CursorShape.PointingHandCursor if key else Qt.CursorShape.ArrowCursor)
            self.update()

    def leaveEvent(self, event: QEvent) -> None:  # type: ignore[override]
        self._hovered = None
        self.update()

    def mousePressEvent(self, event: QMouseEvent) -> None:  # type: ignore[override]
        if event.button() == Qt.MouseButton.LeftButton:
            self._selected = self._key_at(event.position())
            self.update()

    def paintEvent(self, event: QPaintEvent) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#0d1017"))

        area = QRectF(self.rect()).adjusted(46, 46, -46, -46)

        key_positions = physical_layouts[self._layout.physical_layout]

        bottom_right = key_positions[ScanCode.KPENTER]
        total_columns = bottom_right.x + bottom_right.width
        total_rows = bottom_right.y + bottom_right.height
        gap = 8.0
        key_width = (area.width() - gap * (total_columns - 1)) / total_columns
        key_height = min((area.height() - gap * (total_rows - 1)) / total_rows, key_width * 0.92)
        board_height = key_height * total_rows + gap * (total_rows - 1)
        top = area.center().y() - board_height / 2
        self._key_rects.clear()

        chassis = QRectF(area.left() - 16, top - 16, area.width() + 32, board_height + 32)
        painter.setPen(QPen(QColor("#2a3140"), 1))
        painter.setBrush(QColor("#151a24"))
        painter.drawRoundedRect(chassis, 18, 18)

        for key, value in key_positions.items():
            x = area.left() + value.x * (key_width + gap)
            y = top + value.y * (key_height + gap)
            width = value.width * key_width + (value.width - 1) * gap
            height = value.height * key_height + (value.height - 1) * gap
            rect = QRectF(x, y, width, height)
            self._key_rects.append((value, rect))
            label = self._layout.keys.get(key)
            if label:
                label = KeyLabels(
                    primary=label.primary,
                    top_left=label.additional.get(Modifier.SHIFT) if label.additional else None,
                    top_right=label.additional.get(Modifier.CTRL) if label.additional else None,
                    bottom_left=label.additional.get(Modifier.NUMLK) if label.additional else None,
                    bottom_right=label.additional.get(Modifier.ALTGR) if label.additional else None,
                )
            else:
                label = KeyLabels(
                    primary="",
                    top_left=None,
                    top_right=None,
                    bottom_left=None,
                    bottom_right=None,
                )

            self._draw_Key(painter, rect, value, label, value.special_shape)

        painter.end()

    def _draw_Key(self, painter: QPainter, rect: QRectF, key: KeyPosition, labels: KeyLabels, special_shape: bool) -> None:
        is_active = key == self._selected
        is_hovered = key == self._hovered
        if is_active:
            fill, border, label_color = QColor("#5b8cff"), QColor("#9bb7ff"), QColor("#ffffff")
        elif is_hovered:
            fill, border, label_color = QColor("#303b51"), QColor("#627393"), QColor("#f3f6ff")
        else:
            fill, border, label_color = QColor("#202735"), QColor("#394456"), QColor("#d9dfeb")

        painter.setPen(QPen(border, 1))
        painter.setBrush(fill)
        r = 8
        if special_shape:
            wl = rect.width() / 1.5 * 0.3
            bl = rect.left() + wl
            bh = rect.top() + rect.height() / 2 - 4
            path = QPainterPath()
            path.moveTo(rect.left() + r, rect.top())
            path.lineTo(rect.right() - r, rect.top())
            path.quadTo(rect.right(), rect.top(), rect.right(), rect.top() + r)
            path.lineTo(rect.right(), rect.bottom() - r)
            path.quadTo(rect.right(), rect.bottom(), rect.right() - r, rect.bottom())
            path.lineTo(bl + r, rect.bottom())
            path.quadTo(bl, rect.bottom(), bl, rect.bottom() - r)
            path.lineTo(bl, bh + r)
            path.quadTo(bl, bh, bl - r, bh)
            path.lineTo(rect.left() + r, bh)
            path.quadTo(rect.left(), bh, rect.left(), bh - r)
            path.lineTo(rect.left(), rect.top() + r)
            path.quadTo(rect.left(), rect.top(), rect.left() + r, rect.top())
            painter.drawPath(path)
            textrect = QRectF(bl, rect.top(), rect.width() - wl, rect.height())
        else:
            path = QPainterPath()
            path.addRoundedRect(rect, r, r)
            painter.drawPath(path)
            textrect = rect


        label_rects = [
            (textrect, labels.primary),
            (QRectF(textrect.left(), textrect.top(), textrect.width() /2, textrect.height() / 2), labels.top_left),
            (QRectF(textrect.right() - textrect.width() / 2, textrect.top(), textrect.width() / 2, textrect.height() / 2), labels.top_right),
            (QRectF(textrect.left(), textrect.bottom() - textrect.height() / 2, textrect.width() / 2, textrect.height() / 2), labels.bottom_left),
            (QRectF(textrect.right() - textrect.width() / 2, textrect.bottom() - textrect.height() / 2, textrect.width() / 2, textrect.height() / 2), labels.bottom_right),
        ]
        for rect, label in label_rects:
            if label:
                font_size = max(8, min(15, int(min(rect.height(), rect.width()) * (0.18 if label and len(label) > 1 else 0.32))))
                painter.setFont(QFont("Inter", font_size, QFont.Weight.DemiBold))
                painter.setPen(label_color)
                painter.drawText(rect.adjusted(6, 4, -6, -4), Qt.AlignmentFlag.AlignCenter, label)


