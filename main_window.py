import sys
from urllib.request import urlopen

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget

image_source = "https://redragonshop.com/cdn/shop/products/MMOGamingMouse_2.png"


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("M811 Configurator")
        self.resize(960, 540)

        central_widget = QWidget(self)
        layout = QVBoxLayout(central_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        image_label = QLabel()
        image_label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        pixmap = self._load_image()
        if pixmap is not None:
            image_label.setPixmap(pixmap)

        layout.addWidget(image_label)
        self.setCentralWidget(central_widget)

    def _load_image(self) -> QPixmap | None:
        with urlopen(image_source) as response:
            image_data = response.read()

        pixmap = QPixmap()
        if not pixmap.loadFromData(image_data):
            return None

        return pixmap.scaledToWidth(400, Qt.TransformationMode.SmoothTransformation)


def start_app() -> int:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()
