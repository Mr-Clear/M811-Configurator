from PySide6.QtCore import QPoint, QRect, QSize
from PySide6.QtWidgets import (
	QStyle,
	QStyleOptionTab,
	QStylePainter,
	QTabBar,
	QTabWidget,
)


class _HorizontalTabBar(QTabBar):
	"""West-positioned tab bar that draws labels horizontally (not rotated)."""

	def tabSizeHint(self, index: int) -> QSize:
		s = super().tabSizeHint(index)
		return QSize(s.height(), min(s.height(), 24))

	def paintEvent(self, event) -> None:
		painter = QStylePainter(self)
		for index in range(self.count()):
			opt = QStyleOptionTab()
			self.initStyleOption(opt, index)
			r: QRect = opt.rect
			is_selected = bool(opt.state & QStyle.StateFlag.State_Selected)

			shape_opt = QStyleOptionTab()
			self.initStyleOption(shape_opt, index)
			shape_opt.shape = QTabBar.Shape.RoundedSouth
			shape_opt.rect = QRect(QPoint(r.top(), r.left()), QSize(r.height(), r.width()))

			painter.save()
			painter.setClipRect(r.adjusted(0, 0, 3 if is_selected else 0, 0))
			cx, cy = r.center().x(), r.center().y()
			painter.translate(cx, cy)
			painter.rotate(90)
			painter.translate(-cy, -cx)
			painter.drawControl(QStyle.ControlElement.CE_TabBarTabShape, shape_opt)
			painter.restore()

			label_opt = QStyleOptionTab()
			self.initStyleOption(label_opt, index)
			label_opt.rect = r.adjusted(0, -4, 0, 4)
			label_opt.shape = QTabBar.Shape.RoundedNorth
			painter.drawControl(QStyle.ControlElement.CE_TabBarTabLabel, label_opt)


# Re-export as a plain QTabWidget subclass so callers can use it as a drop-in
class VerticalTabWidget(QTabWidget):
	def __init__(self, parent=None) -> None:
		super().__init__(parent)
		self.setTabBar(_HorizontalTabBar())
		self.setTabPosition(QTabWidget.TabPosition.West)
