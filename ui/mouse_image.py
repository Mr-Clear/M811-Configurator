from __future__ import annotations

import logging
import xml.etree.ElementTree as ET

import svgpathtools
from PySide6.QtCore import QEvent, QPointF, QRectF, Qt, Signal, Slot
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import QLabel, QWidget

from ui.downloader import download

logger = logging.getLogger(__name__)

_XLINK_HREF = '{http://www.w3.org/1999/xlink}href'
_HREF = 'href'


def _svg_path_to_painter_path(d: str) -> QPainterPath:
    """Convert an SVG path `d` string to a QPainterPath.

    svgpathtools has no Move segment type — implicit moves are detected by
    comparing each segment's start point against the previous segment's end.
    """
    path = QPainterPath()
    prev_end: complex | None = None
    for seg in svgpathtools.parse_path(d):
        # Start a new subpath whenever there is a discontinuity (implicit M)
        if prev_end is None or seg.start != prev_end:
            path.moveTo(seg.start.real, seg.start.imag)

        if isinstance(seg, svgpathtools.Line):
            path.lineTo(seg.end.real, seg.end.imag)
        elif isinstance(seg, svgpathtools.CubicBezier):
            path.cubicTo(
                seg.control1.real, seg.control1.imag,
                seg.control2.real, seg.control2.imag,
                seg.end.real, seg.end.imag,
            )
        elif isinstance(seg, svgpathtools.QuadraticBezier):
            path.quadTo(
                seg.control.real, seg.control.imag,
                seg.end.real, seg.end.imag,
            )
        else:  # isinstance(seg, svgpathtools.Arc)
            for cubic in seg.as_cubic_curves():
                path.cubicTo(
                    cubic.control1.real, cubic.control1.imag,
                    cubic.control2.real, cubic.control2.imag,
                    cubic.end.real, cubic.end.imag,
                )

        prev_end = seg.end
    path.closeSubpath()
    return path


class MouseImageWidget(QLabel):
    """Displays a mouse image with clickable/highlightable button areas defined by an SVG file."""

    button_clicked = Signal(int)
    button_hovered = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._base_pixmap: QPixmap | None = None
        self._image_rect: QRectF = QRectF()
        self._svg_size: tuple[float, float] = (1.0, 1.0)
        self._scale: float = 1.0
        self._fixed_width: float | None = None
        self._fixed_height: float | None = None
        self._paths: list[QPainterPath] = []
        self._selected: int = -1
        self._hovered: int = -1
        self.setMouseTracking(True)

    @property
    def fixed_width(self) -> float | None:
        return self._fixed_width

    @fixed_width.setter
    def fixed_width(self, value: float | None) -> None:
        self._fixed_width = value
        if value is not None:
            self._fixed_height = None
        self._recompute_scale()

    @property
    def fixed_height(self) -> float | None:
        return self._fixed_height

    @fixed_height.setter
    def fixed_height(self, value: float | None) -> None:
        self._fixed_height = value
        if value is not None:
            self._fixed_width = None
        self._recompute_scale()

    @Slot(str)
    def load_svg(self, svg_path: str) -> None:
        """Parse an SVG file.

        Expected SVG structure:
        - Root ``width``/``height`` attributes define the coordinate space.
        - An ``<image id="pixmap">`` element whose ``xlink:href`` (or ``href``)
          is a URL to the mouse photo.  Its ``x``, ``y``, ``width``, ``height``
          attributes position the photo inside the SVG canvas.
        - ``<path id="button1">``, ``<path id="button2">`` … define hit areas.
          Missing indices are skipped; the list is built up to the highest found.
        """
        logger.debug(f"Loading SVG: {svg_path}")
        tree = ET.parse(svg_path)
        root = tree.getroot()

        # SVG width / height
        try:
            self._svg_size = (float(root.get('width', 1)),
                              float(root.get('height', 1)))
        except ValueError:
            self._svg_size = (1.0, 1.0)

        # Collect button paths by index
        button_map: dict[int, QPainterPath] = {}
        image_url: str | None = None
        self._image_rect = QRectF(0, 0, self._svg_size[0], self._svg_size[1])

        for elem in root.iter():
            tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
            elem_id = elem.get('id', '')

            if tag == 'image' and elem_id == 'pixmap':
                href = elem.get(_XLINK_HREF) or elem.get(_HREF, '')
                if href:
                    image_url = href
                try:
                    self._image_rect = QRectF(
                        float(elem.get('x', 0)),
                        float(elem.get('y', 0)),
                        float(elem.get('width', self._svg_size[0])),
                        float(elem.get('height', self._svg_size[1])),
                    )
                except ValueError:
                    pass
                continue

            if not elem_id.startswith('button'):
                continue
            try:
                btn_index = int(elem_id[len('button'):]) - 1  # "button1" → 0
            except ValueError:
                continue
            if btn_index < 0:
                continue

            d: str | None = None
            if tag == 'path':
                d = elem.get('d')
            elif tag in ('polygon', 'polyline'):
                points = elem.get('points', '')
                coords = points.replace(',', ' ').split()
                if len(coords) >= 4:
                    pairs = list(zip(coords[::2], coords[1::2]))
                    d = 'M ' + ' L '.join(f'{x},{y}' for x, y in pairs) + ' Z'

            if d:
                button_map[btn_index] = _svg_path_to_painter_path(d)

        # Build contiguous list, leaving gaps as empty paths
        if button_map:
            max_index = max(button_map.keys())
            self._paths = [button_map.get(i, QPainterPath())
                           for i in range(max_index + 1)]
        else:
            self._paths = []

        self._base_pixmap = None
        self._recompute_scale()

        if image_url:
            download(image_url, self._on_image_downloaded)

    @Slot(float)
    def set_scale(self, scale: float) -> None:
        self._fixed_width = None
        self._fixed_height = None
        self._scale = max(scale, 0.01)
        self._apply_size()
        self._redraw()

    @Slot(int)
    def set_selected_button(self, index: int) -> None:
        if self._selected != index:
            self._selected = index
            self._redraw()

    # ------------------------------------------------------------------ #
    # Internals                                                            #
    # ------------------------------------------------------------------ #

    def _recompute_scale(self) -> None:
        """Recalculate _scale from _fixed_width/_fixed_height and current SVG size, then redraw."""
        sw, sh = self._svg_size
        if self._fixed_width is not None and sw > 0:
            self._scale = self._fixed_width / sw
        elif self._fixed_height is not None and sh > 0:
            self._scale = self._fixed_height / sh
        self._apply_size()
        self._redraw()

    def _apply_size(self) -> None:
        sw, sh = self._svg_size
        self.setFixedSize(int(sw * self._scale), int(sh * self._scale))

    def _path_index_at(self, pos: QPointF) -> int:
        # Map widget pixels → SVG coords
        svg_pos = QPointF(pos.x() / self._scale, pos.y() / self._scale)
        for i, path in enumerate(self._paths):
            if not path.isEmpty() and path.contains(svg_pos):
                return i
        return -1

    def _on_image_downloaded(self, data: bytes | Exception) -> None:
        if isinstance(data, Exception):
            logger.error(f"MouseImageWidget: failed to download image: {data}")
            return
        pixmap = QPixmap()
        if not pixmap.loadFromData(data):
            logger.error("MouseImageWidget: failed to decode image data")
            return
        self._base_pixmap = pixmap
        self._apply_size()
        self._redraw()

    def _redraw(self) -> None:
        sw, sh = self._svg_size
        s = self._scale
        canvas = QPixmap(int(sw * s), int(sh * s))
        canvas.fill(Qt.GlobalColor.transparent)
        painter = QPainter(canvas)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.scale(s, s)

        # Draw the photo scaled into the <image> rect
        if self._base_pixmap is not None:
            r = self._image_rect
            painter.drawPixmap(
                int(r.x()), int(r.y()), int(r.width()), int(r.height()),
                self._base_pixmap,
            )

        # Draw button overlays
        for i, path in enumerate(self._paths):
            if path.isEmpty():
                continue
            if i == self._selected:
                if i == self._hovered:
                    painter.fillPath(path, QColor(255, 200, 120, 180))
                    painter.setPen(QColor(255, 140, 0, 220))
                else:
                    painter.fillPath(path, QColor(255, 165, 64, 120))
                    painter.setPen(QColor(255, 140, 0, 200))
                painter.drawPath(path)
            elif i == self._hovered:
                painter.fillPath(path, QColor(255, 255, 255, 60))
                painter.setPen(QColor(255, 255, 255, 150))
                painter.drawPath(path)

        painter.end()
        super().setPixmap(canvas)

    # ------------------------------------------------------------------ #
    # Events                                                               #
    # ------------------------------------------------------------------ #

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        hovered = self._path_index_at(QPointF(event.position()))
        if hovered != self._hovered:
            self._hovered = hovered
            self._redraw()
            self.button_hovered.emit(hovered)
        super().mouseMoveEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        if self._hovered != -1:
            self._hovered = -1
            self._redraw()
            self.button_hovered.emit(-1)
        super().leaveEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            index = self._path_index_at(QPointF(event.position()))
            if index >= 0:
                self.button_clicked.emit(index)
        super().mousePressEvent(event)
