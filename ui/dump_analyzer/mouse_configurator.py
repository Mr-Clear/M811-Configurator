from typing import Any

from PySide6.QtCore import QModelIndex, QRect, QRegularExpression, Qt, Signal
from PySide6.QtGui import QPainter, QRegularExpressionValidator
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QFormLayout,
                               QHBoxLayout, QLabel, QLineEdit, QListWidget,
                               QListWidgetItem, QSpinBox, QStyle,
                               QStyledItemDelegate, QStyleOptionViewItem,
                               QToolButton, QVBoxLayout, QWidget)


class MouseConfigurator(QWidget):
    """Configure mouse properties like button names."""

    value_changed = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.mouse_name_input: QLineEdit
        self.image_input: QLineEdit
        self.buttons_list: QListWidget
        self.buttons_add: QToolButton
        self.buttons_remove: QToolButton
        self.buttons_move_up: QToolButton
        self.buttons_move_down: QToolButton
        self.mode_count_spinbox: QSpinBox
        self.macro_count_spinbox: QSpinBox
        self.steps_per_macro_spinbox: QSpinBox

        self._init_ui()

    def _init_ui(self):
        layout = QFormLayout(self)
        layout.setContentsMargins(8, 4, 8, 8)
        layout.setSpacing(4)

        self.mouse_name_input = QLineEdit(self)
        self.mouse_name_input.textChanged.connect(self.value_changed)
        layout.addRow("Model Name:", self.mouse_name_input)

        id_layout = QHBoxLayout()
        id_layout.setSpacing(0)
        self.vendor_id_input = QLineEdit(self)
        self.vendor_id_input.setValidator(QRegularExpressionValidator(QRegularExpression(r"^[0-9A-Fa-f]{4}$"), self))
        self.vendor_id_input.textChanged.connect(self.value_changed)
        id_layout.addWidget(self.vendor_id_input)
        id_layout.addWidget(QLabel(":"))
        self.product_id_input = QLineEdit(self)
        self.product_id_input.setValidator(QRegularExpressionValidator(QRegularExpression(r"^[0-9A-Fa-f]{4}$"), self))
        self.product_id_input.textChanged.connect(self.value_changed)
        id_layout.addWidget(self.product_id_input)
        layout.addRow("USB ID:", id_layout)

        image_layout = QHBoxLayout()
        self.image_input = QLineEdit(self)
        self.image_input.textChanged.connect(self.value_changed)
        image_layout.addWidget(self.image_input)
        image_button = QToolButton(self)
        image_button.setText("...")
        image_layout.addWidget(image_button)
        layout.addRow("Image:", image_layout)

        layout.addRow(QLabel("Buttons:"))
        buttons_layout = QHBoxLayout()
        buttons_controls_layout = QVBoxLayout()
        self.buttons_list = QListWidget(self)
        self.buttons_list.setItemDelegate(ButtonItemDelegate(self))
        self.buttons_list.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked)
        self.buttons_list.itemChanged.connect(self.value_changed)
        buttons_layout.addWidget(self.buttons_list)
        buttons_layout.addLayout(buttons_controls_layout)
        self.buttons_add = QToolButton(self)
        self.buttons_add.setText("➕")
        self.buttons_add.clicked.connect(self._add_button)
        buttons_controls_layout.addWidget(self.buttons_add)
        self.buttons_remove = QToolButton(self)
        self.buttons_remove.setText("➖")
        self.buttons_remove.clicked.connect(self._remove_button)
        buttons_controls_layout.addWidget(self.buttons_remove)
        self.buttons_move_up = QToolButton(self)
        self.buttons_move_up.setText("⬆️")
        self.buttons_move_up.clicked.connect(self._move_button_up)
        buttons_controls_layout.addWidget(self.buttons_move_up)
        self.buttons_move_down = QToolButton(self)
        self.buttons_move_down.setText("⬇️")
        self.buttons_move_down.clicked.connect(self._move_button_down)
        buttons_controls_layout.addWidget(self.buttons_move_down)
        layout.addRow(buttons_layout)

        self.mode_count_spinbox = QSpinBox(self)
        self.mode_count_spinbox.setMinimum(1)
        self.mode_count_spinbox.setMaximum(10)
        self.mode_count_spinbox.valueChanged.connect(self.value_changed)
        layout.addRow("Mode Count:", self.mode_count_spinbox)

        self.macro_count_spinbox = QSpinBox(self)
        self.macro_count_spinbox.setMinimum(0)
        self.macro_count_spinbox.setMaximum(100)
        self.macro_count_spinbox.valueChanged.connect(self.value_changed)
        layout.addRow("Macro Count:", self.macro_count_spinbox)

        self.steps_per_macro_spinbox = QSpinBox(self)
        self.steps_per_macro_spinbox.setMinimum(1)
        self.steps_per_macro_spinbox.setMaximum(100)
        self.steps_per_macro_spinbox.valueChanged.connect(self.value_changed)
        layout.addRow("Steps per Macro:", self.steps_per_macro_spinbox)

    def _add_button(self):
        item = QListWidgetItem("New Button")
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
        self.buttons_list.addItem(item)
        self.buttons_list.setCurrentItem(item)
        self.buttons_list.editItem(item)
        self.value_changed.emit()

    def _remove_button(self):
        current_row = self.buttons_list.currentRow()
        if current_row >= 0:
            self.buttons_list.takeItem(current_row)
            self.value_changed.emit()

    def _move_button_up(self):
        current_row = self.buttons_list.currentRow()
        if current_row > 0:
            item = self.buttons_list.takeItem(current_row)
            self.buttons_list.insertItem(current_row - 1, item)
            self.buttons_list.setCurrentRow(current_row - 1)
            self.value_changed.emit()

    def _move_button_down(self):
        current_row = self.buttons_list.currentRow()
        if current_row >= 0 and current_row < self.buttons_list.count() - 1:
            item = self.buttons_list.takeItem(current_row)
            self.buttons_list.insertItem(current_row + 1, item)
            self.buttons_list.setCurrentRow(current_row + 1)
            self.value_changed.emit()

    def get_data(self) -> dict[str, Any]:
        """Get the current configuration data as a dictionary."""
        return {
            "mouse_name": self.mouse_name_input.text(),
            "vendor_id": self.vendor_id_input.text(),
            "product_id": self.product_id_input.text(),
            "image": self.image_input.text(),
            "buttons": [self.buttons_list.item(i).text() for i in range(self.buttons_list.count())],
            "mode_count": self.mode_count_spinbox.value(),
            "macro_count": self.macro_count_spinbox.value(),
            "steps_per_macro": self.steps_per_macro_spinbox.value(),
        }

    def set_data(self, data: dict[str, Any]):
        """Set the current configuration data from a dictionary."""
        self.mouse_name_input.setText(data["mouse_name"])
        self.vendor_id_input.setText(data["vendor_id"])
        self.product_id_input.setText(data["product_id"])
        self.image_input.setText(data["image"])
        self.buttons_list.clear()
        for button_name in data["buttons"]:
            item = QListWidgetItem(button_name)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.buttons_list.addItem(item)
        self.mode_count_spinbox.setValue(data["mode_count"])
        self.macro_count_spinbox.setValue(data["macro_count"])
        self.steps_per_macro_spinbox.setValue(data["steps_per_macro"])

class ButtonItemDelegate(QStyledItemDelegate):
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None: # type: ignore[override]
        value = index.model().data(index, Qt.ItemDataRole.DisplayRole)
        if value is None:
            return
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        opt.text = ''
        style = opt.widget.style() if opt.widget else QApplication.style()
        style.drawControl(QStyle.ControlElement.CE_ItemViewItem, opt, painter, opt.widget)

        max_rows = index.model().rowCount()
        max_number_length = len(str(max_rows))
        max_number_width = option.fontMetrics.horizontalAdvance("8" * max_number_length + ": ")
        number = index.row() + 1
        number_text = f"{number}: "
        r = option.rect
        painter.drawText(
            QRect(r.left(), r.top(), max_number_width, r.height()),
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            number_text
        )
        painter.drawText(
            QRect(r.left() + max_number_width, r.top(), r.width() - max_number_width, r.height()),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            value
        )
