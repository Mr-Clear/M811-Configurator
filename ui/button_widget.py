'''Custom widget to show and modify mouse button data.'''
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QLabel, QVBoxLayout, QWidget

from ui.mouse_data import Button, ButtonOff


class ButtonWidget(QWidget):
    type_changed = Signal(Button)
    data_changed = Signal()

    '''Widget to show and modify mouse button data.'''
    def __init__(self, data: Button, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.data = data

        self.type_combo = QComboBox()
        for button_type in Button.get_all_button_types():
            self.type_combo.addItem(button_type.type_name())
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)

        self.content_container = QWidget()
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(0, 0, 0, 0)

        layout = QVBoxLayout(self)
        layout.addWidget(self.type_combo)
        layout.addWidget(self.content_container)
        layout.addStretch(1)
        self.set_data(data)

    def set_data(self, data: Button) -> None:
        '''Set the button data to display.'''
        self.data = data

        self.type_combo.blockSignals(True)
        button_types = Button.get_all_button_types()
        try:
            index = button_types.index(type(data))
        except ValueError:
            index = 0
        self.type_combo.setCurrentIndex(index)
        self.type_combo.blockSignals(False)

        content_widget = ButtonWidget._ContentWidget.from_button(data)
        if self.content_layout.count() > 0:
            old_item = self.content_layout.takeAt(0)
            if old_item is not None:
                old_widget = old_item.widget()
                if old_widget is not None:
                    old_widget.deleteLater()
        self.content_layout.addWidget(content_widget)

    def _on_type_changed(self, index: int) -> None:
        '''Handle the user changing the button type from the combo box.'''
        new_type = Button.get_all_button_types()[index]
        self.set_data(new_type(None))


    class _ContentWidget(QWidget):
        data_changed = Signal()

        '''Widget to show the content of a button.'''
        def __init__(self, parent: QWidget | None = None) -> None:
            super().__init__(parent)

        @staticmethod
        def from_button(data: Button, parent: QWidget | None = None) -> ButtonWidget._ContentWidget:
            '''Create a content widget for the given button data.'''
            if isinstance(data, ButtonOff):
                return ButtonWidget._ButtonOffContentWidget(data, parent)
            else:
                return QWidget(parent)  # type: ignore[return-value]

    class _ButtonOffContentWidget(_ContentWidget):
        '''Widget to show the content of a button that is off.'''
        def __init__(self, data: ButtonOff, parent: QWidget | None = None) -> None:
            super().__init__(parent)
            assert data.button_type == ButtonOff
