"""A self-contained PySide6 keyboard-layout renderer.

Run this file directly to open the demo application:
    python ui/keyboard_image.py
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from PySide6.QtCore import QEvent, QObject, QPointF, QRectF, Qt, Signal
from PySide6.QtGui import (QColor, QFont, QKeyEvent, QMouseEvent, QPainter,
                           QPainterPath, QPaintEvent, QPen, QWindow)
from PySide6.QtWidgets import QApplication, QWidget

from .layouts import KeyboardLayout, Modifier, known_layouts
from .physical_layout import PhysicalLayout
from .usb_hid import (ModifierCode, ScanCode, modifier_keys,
                      native_scan_code_to_hid)


@dataclass
class KeyColors:
    background: QColor
    border: QColor
    text: QColor

@dataclass
class KeyboardColors:
    background: QColor
    border: QColor
    keyboard_color: QColor
    key: KeyColors
    key_hovered: KeyColors
    key_active: KeyColors
    key_down: KeyColors
    key_up: KeyColors

keyboard_colors = KeyboardColors(
    background=QColor("#0d1017"),
    border=QColor("#2a3140"),
    keyboard_color=QColor("#151a24"),
    key=KeyColors(
        background=QColor("#202735"),
        border=QColor("#394456"),
        text=QColor("#d9dfeb")
    ),
    key_hovered=KeyColors(
        background=QColor("#303b51"),
        border=QColor("#627393"),
        text=QColor("#f3f6ff")
    ),
    key_active=KeyColors(
        background=QColor("#5b8cff"),
        border=QColor("#9bb7ff"),
        text=QColor("#ffffff")
    ),
    key_down=KeyColors(
        background=QColor("#cc3c3c"),
        border=QColor("#ff6b6b"),
        text=QColor("#ffffff")
    ),
    key_up=KeyColors(
        background=QColor("#3ccc3c"),
        border=QColor("#6bff6b"),
        text=QColor("#ffffff")
    ),

)

@dataclass(frozen=True)
class KeyPosition:
    x: float
    y: float
    width: float = 1.0
    height: float = 1.0
    special_shape: bool = False   # Currently, True means the key is the Enter key on an ISO layout.


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


class Align(Enum):
    Center = Qt.AlignmentFlag.AlignCenter
    Top = Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter
    TopLeft = Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
    Left = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
    BottomLeft = Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft
    Bottom = Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter
    BottomRight = Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight
    Right = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
    TopRight = Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight


class KeyboardWidget(QWidget):
    """Paints a responsive keyboard and highlights the last clicked key."""

    hover_changed = Signal(ScanCode) # | None
    key_down = Signal(ScanCode, ModifierCode)
    key_up = Signal(ScanCode)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(980, 460)
        self.setMouseTracking(True)
        self._hovered: ScanCode | None = None
        self._selected: set[ScanCode] = set()
        self._pressed: ScanCode | None = None
        self._key_rects: list[tuple[ScanCode, KeyPosition, QRectF]] = []
        self._layout = list(known_layouts().values())[0]

        instance = QApplication.instance()
        assert instance is not None
        instance.installEventFilter(self)

    def _key_at(self, point: QPointF) -> ScanCode | None:
        for key, _key_position, rect in self._key_rects:
            if rect.contains(point):
                return key
        return None

    def _set_hovered(self, scan_code: ScanCode | None) -> None:
        if self._hovered != scan_code:
            self._hovered = scan_code
            self.hover_changed.emit(scan_code)

            self.update()

    @property
    def keyboard_layout(self) -> KeyboardLayout:
        return self._layout

    @keyboard_layout.setter
    def keyboard_layout(self, layout: KeyboardLayout) -> None:
        self._layout = layout
        self.update()

    @property
    def hovered_key(self) -> ScanCode | None:
        return self._hovered

    @property
    def pressed_keys(self) -> set[ScanCode]:
        return self._selected

    @property
    def pressed_modifiers(self) -> ModifierCode:
        modifiers = ModifierCode(0)
        for key in modifier_keys:
            if key in self._selected:
                modifiers |= modifier_keys[key]
        return modifiers

    def set_key_down(self, key: ScanCode):
        self._selected.add(key)
        self.key_down.emit(key, self.pressed_modifiers)
        self.update()

    def set_key_up(self, key: ScanCode):
        self._selected.discard(key)
        self.key_up.emit(key)
        self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # type: ignore[override]
        key = self._key_at(event.position())
        if key != self._hovered:
            self._set_hovered(key)
            self.setCursor(Qt.CursorShape.PointingHandCursor if key else Qt.CursorShape.ArrowCursor)

    def leaveEvent(self, event: QEvent) -> None:  # type: ignore[override]
        self._set_hovered(None)

    def mousePressEvent(self, event: QMouseEvent) -> None:  # type: ignore[override]
        key = self._key_at(event.position())
        if not key:
            return
        if event.button() == Qt.MouseButton.LeftButton:
            self._pressed = key
            if not key in self._selected:
                self.set_key_down(key)
            self.update()
        elif event.button() == Qt.MouseButton.RightButton:
            if key in self._selected:
                self.set_key_up(key)
            else:
                self.set_key_down(key)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # type: ignore[override]
        if event.button() == Qt.MouseButton.LeftButton:
            if self._pressed:
                self.set_key_up(self._pressed)
                self._pressed = None

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), keyboard_colors.background)

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
        painter.setPen(QPen(keyboard_colors.border, 1))
        painter.setBrush(keyboard_colors.keyboard_color)
        painter.drawRoundedRect(chassis, 18, 18)

        additional_modifiers = {
            **self._layout.modifiers,
            ScanCode.CAPSLOCK: Modifier.SHIFT,
            ScanCode.NUMLOCK: Modifier.NUMLK,
        }
        modifiers: Modifier = Modifier(0)
        for scan_code, modifier in additional_modifiers.items():
            if scan_code in self._selected:
                modifiers |= modifier

        for key, value in key_positions.items():
            x = area.left() + value.x * (key_width + gap)
            y = top + value.y * (key_height + gap)
            width = value.width * key_width + (value.width - 1) * gap
            height = value.height * key_height + (value.height - 1) * gap
            rect = QRectF(x, y, width, height)
            self._key_rects.append((key, value, rect))

            if key in self._selected:
                colors = keyboard_colors.key_active
            elif key == self._hovered:
                colors = keyboard_colors.key_hovered
            else:
                colors = keyboard_colors.key
            draw_key(painter, rect, key, modifiers, self._layout, colors, special_shape=value.special_shape)

        painter.end()

    def eventFilter(self,  watched: QObject, event: QEvent):
        if event.type() == QEvent.Type.KeyPress:
            assert isinstance(event, QKeyEvent)
            if not event.isAutoRepeat() and isinstance(watched, QWindow):
                scan_code = native_scan_code_to_hid(event.nativeScanCode())
                if scan_code:
                    self.set_key_down(scan_code)
        elif event.type() == QEvent.Type.KeyRelease:
            assert isinstance(event, QKeyEvent)
            if not event.isAutoRepeat() and isinstance(watched, QWindow):
                scan_code = native_scan_code_to_hid(event.nativeScanCode())
                if scan_code:
                    self.set_key_up(scan_code)

        return super().eventFilter(watched, event)


class KeyWidget(QWidget):
    """A self-contained widget that paints a single key."""

    def __init__(self,
                 scan_code: ScanCode | None,
                 modifiers: Modifier | ModifierCode,
                 keyboard_layout: KeyboardLayout,
                 colors: KeyColors,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(32, 32)
        self._key: ScanCode | None = scan_code
        self._layout: KeyboardLayout = keyboard_layout
        self._layout_key = self._layout.keys.get(scan_code) if scan_code else None
        self._modifiers: Modifier
        if isinstance(modifiers, Modifier):
            self._modifiers = modifiers
        else:
            self._modifiers = self._layout.modifiers_from_modifier_codes(modifiers)
        self._colors: KeyColors = colors

    @property
    def scan_code(self) -> ScanCode | None:
        return self._key
    @scan_code.setter
    def scan_code(self, scan_code: ScanCode | None) -> None:
        self._key = scan_code
        self._layout_key = self._layout.keys.get(scan_code) if scan_code else None
        self.update()

    @property
    def modifiers(self) -> Modifier:
        return self._modifiers
    @modifiers.setter
    def modifiers(self, modifiers: Modifier | ModifierCode) -> None:
        if isinstance(modifiers, Modifier):
            self._modifiers = modifiers
        else:
            self._modifiers = self._layout.modifiers_from_modifier_codes(modifiers)
        self.update()

    @property
    def keyboard_layout(self) -> KeyboardLayout:
        return self._layout
    @keyboard_layout.setter
    def keyboard_layout(self, layout: KeyboardLayout) -> None:
        self._layout = layout
        self._layout_key = self._layout.keys.get(self._key) if self._key else None
        self.update()

    @property
    def colors(self) -> KeyColors:
        return self._colors
    @colors.setter
    def colors(self, colors: KeyColors) -> None:
        self._colors = colors
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        area = QRectF(self.rect())
        draw_key(painter, area, self._key, self._modifiers, self._layout, self._colors, special_shape=False)


def draw_key(painter: QPainter, rect: QRectF, key: ScanCode | None, modifiers: Modifier, keyboard_layout: KeyboardLayout, colors: KeyColors, special_shape: bool):
    size = min(rect.width(), rect.height())
    painter.setPen(QPen(colors.border, 2))
    painter.setBrush(colors.background)
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

    if not key:
        return

    layout_key = keyboard_layout.keys.get(key)
    layout_key_labels = layout_key.labels if layout_key else {}
    labels: dict[Align, str] = {}
    primary_position = Align.Center if key.is_numpad_key or layout_key and (layout_key.is_letter or not layout_key.additional) else Align.BottomLeft
    modifier_positions = {
        Modifier.NONE: primary_position,
        Modifier.SHIFT: Align.TopLeft,
        Modifier.CTRL: Align.TopRight,
        Modifier.NUMLK: Align.Bottom,
        Modifier.ALTGR: Align.BottomRight,
    }
    if layout_key:
        for position, alignment in modifier_positions.items():
            if position in layout_key_labels:
                labels[alignment] = layout_key_labels[position]
        for modifier in modifiers:
            if modifier in modifier_positions and modifier_positions[modifier] in labels and \
                primary_position in labels:
                    primary = labels[primary_position]
                    labels[primary_position] = labels[modifier_positions[modifier]]
                    labels[modifier_positions[modifier]] = primary
                    break

    no_center = Align.Center not in labels
    for alignment, label in labels.items():
        if label:
            textrect_adjusted = textrect.adjusted(6, 4, -6, -4)
            if no_center:
                textrect_adjusted = textrect_adjusted.adjusted(size * 0.1, 0, -size * 0.1, 0)
            font_size = size * 0.4
            if alignment != alignment.Center:
                font_size *= 0.65 if no_center else 0.5
            if len(label) > 1:
                font_size *= 0.7
            if len(label) > 3:
                font_size *= 0.7
            font = QFont("Inter", 12, QFont.Weight.DemiBold)
            font.setPointSizeF(font_size)
            painter.setFont(font)
            painter.setPen(colors.text)
            painter.drawText(textrect_adjusted, alignment.value, label)


