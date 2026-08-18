
import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QApplication, QComboBox, QDockWidget,
                               QHBoxLayout, QMainWindow, QWidget)

from ui.keyboard.keyboard_widget import KeyboardWidget
from ui.keyboard.layouts import known_layouts


class KeyboardWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Keyboard Layout")
        self._keyboard_widget = KeyboardWidget()
        self.setCentralWidget(self._keyboard_widget)

        top_widget = QDockWidget()
        top_container = QWidget()
        top_layout = QHBoxLayout()
        top_container.setLayout(top_layout)
        top_widget.setWidget(top_container)
        self.layout_selector = QComboBox()
        for layout in known_layouts().values():
            self.layout_selector.addItem(layout.name, layout)
        top_layout.addStretch()
        top_layout.addWidget(self.layout_selector)
        top_layout.addStretch()
        self.layout_selector.currentIndexChanged.connect(self.on_layout_changed)
        self.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea, top_widget)

        self.resize(1500, 640)

    def on_layout_changed(self, index: int) -> None:
        layout = self.layout_selector.itemData(index)
        self._keyboard_widget.set_layout(layout)


def start_app() -> int:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = KeyboardWindow()
    window.show()
    return app.exec()
