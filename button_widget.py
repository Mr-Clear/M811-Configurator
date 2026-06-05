from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget


Button = list[int]


class ButtonWidget(QWidget):
	def __init__(self, data: Button, parent=None) -> None:
		super().__init__(parent)
		self._label = QLabel()
		layout = QHBoxLayout(self)
		layout.addWidget(self._label)
		self.set_data(data)

	def set_data(self, data: bytes) -> None:
		self._label.setText(" ".join(f"{b:02X}" for b in data[:4]))
