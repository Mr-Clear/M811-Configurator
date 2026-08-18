import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (QApplication, QComboBox, QHBoxLayout, QLayout,
                               QMainWindow, QScrollArea, QVBoxLayout, QWidget)

from ui.keyboard.keyboard_widget import (KeyboardWidget, KeyWidget, Modifier,
                                         keyboard_colors)
from ui.keyboard.layouts import known_layouts
from ui.keyboard.usb_hid import ModifierCode, ScanCode


class KeyboardWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Keyboard Layout")

        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        top_layout = QHBoxLayout()
        self._keyboard_layout_selector = QComboBox()
        for layout in known_layouts().values():
            self._keyboard_layout_selector.addItem(layout.name, layout)
        top_layout.addStretch()
        top_layout.addWidget(self._keyboard_layout_selector)
        top_layout.addStretch()
        self._keyboard_layout_selector.currentIndexChanged.connect(self.on_layout_changed)
        main_layout.addLayout(top_layout)

        self._keyboard_widget = KeyboardWidget()
        main_layout.addWidget(self._keyboard_widget)

        self._pressed_keys_widget = QWidget()
        self._pressed_keys_widget.setMaximumHeight(50)
        self._pressed_keys_layout = QHBoxLayout()
        self._pressed_keys_layout.setContentsMargins(0, 0, 0, 0)
        self._pressed_keys_layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        self._pressed_keys_widget.setLayout(self._pressed_keys_layout)
        self._pressed_keys_widget_scroll_area = QScrollArea()
        self._pressed_keys_widget_scroll_area.setWidgetResizable(False)
        self._pressed_keys_widget_scroll_area.setWidget(self._pressed_keys_widget)
        main_layout.addWidget(self._pressed_keys_widget_scroll_area)

        self.resize(1500, 640)

        self._keyboard_widget.key_down.connect(self.on_key_down)
        self._keyboard_widget.key_up.connect(self.on_key_up)

    def on_layout_changed(self, index: int) -> None:
        layout = self._keyboard_layout_selector.itemData(index)
        self._keyboard_widget.keyboard_layout = layout

    def on_key_down(self, key: ScanCode, modifier_codes: ModifierCode):
        modifiers = self._keyboard_widget.keyboard_layout.modifiers_from_modifier_codes(modifier_codes)
        widget = KeyWidget(key, modifiers, self._keyboard_widget.keyboard_layout, keyboard_colors.key_down)
        self._add_key_widget(widget)

    def on_key_up(self, key: ScanCode):
        widget = KeyWidget(key, Modifier.NONE, self._keyboard_widget.keyboard_layout, keyboard_colors.key_up)
        self._add_key_widget(widget)

    def _add_key_widget(self, widget: KeyWidget):
        widget.setFixedSize(widget.minimumSize())
        self._pressed_keys_layout.addWidget(widget)
        horizontal_scroll_bar = self._pressed_keys_widget_scroll_area.horizontalScrollBar()
        QTimer.singleShot(0, lambda: horizontal_scroll_bar.setValue(horizontal_scroll_bar.maximum()))

def start_app() -> int:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = KeyboardWindow()
    window.show()
    return app.exec()
