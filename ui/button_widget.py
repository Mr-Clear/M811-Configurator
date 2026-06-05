'''Custom widget to show and modify mouse button data.'''
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

Button = list[int]


class ButtonWidget(QWidget):
    '''Widget to show and modify mouse button data.'''
    def __init__(self, data: Button, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._label = QLabel()
        layout = QHBoxLayout(self)
        layout.addWidget(self._label)
        self.set_data(data)

    def set_data(self, data: Button) -> None:
        '''Set the button data to display.'''
        self._label.setText(" ".join(f"{b:02X}" for b in data[:4]))
