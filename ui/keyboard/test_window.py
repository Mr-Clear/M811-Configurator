import sys

from PySide6.QtWidgets import (QApplication, QComboBox, QHBoxLayout,
                               QMainWindow, QVBoxLayout, QWidget)

from ui.keyboard.keyboard_widget import KeyboardWidget
from ui.keyboard.layouts import known_layouts


class KeyboardWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Keyboard Layout")

        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        top_layout = QHBoxLayout()
        self.keyboard_layout_selector = QComboBox()
        for layout in known_layouts().values():
            self.keyboard_layout_selector.addItem(layout.name, layout)
        top_layout.addStretch()
        top_layout.addWidget(self.keyboard_layout_selector)
        top_layout.addStretch()
        self.keyboard_layout_selector.currentIndexChanged.connect(self.on_layout_changed)
        main_layout.addLayout(top_layout)

        self._keyboard_widget = KeyboardWidget()
        main_layout.addWidget(self._keyboard_widget)

        self.resize(1500, 640)

    def on_layout_changed(self, index: int) -> None:
        layout = self.keyboard_layout_selector.itemData(index)
        self._keyboard_widget.keyboard_layout = layout


def start_app() -> int:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = KeyboardWindow()
    window.show()
    return app.exec()
