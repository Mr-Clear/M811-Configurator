import sys

from PySide6.QtWidgets import QApplication, QMainWindow


class MainWindow(QMainWindow):
	def __init__(self) -> None:
		super().__init__()
		self.setWindowTitle("M811 Configurator")
		self.resize(960, 540)


def start_app() -> int:
	app = QApplication(sys.argv)
	window = MainWindow()
	window.show()
	return app.exec()
