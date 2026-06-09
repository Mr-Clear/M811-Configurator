'''Custom widget to show and modify mouse button data.'''
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QCheckBox, QComboBox, QGridLayout, QHBoxLayout,
                               QLabel, QRadioButton, QSlider, QSpinBox,
                               QVBoxLayout, QWidget)

from ui.keyboard import Modifier
from ui.mouse_data import (ButtomCustom, Button, ButtonFireKey, ButtonKeyPress,
                           ButtonMacro, ButtonMouseButton, ButtonMouseFunction,
                           ButtonOff, ButtonSniper, ButtonSpecialKey)


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
            widget_name = f'_{type(data).__name__}ContentWidget'

            widget_class = getattr(ButtonWidget, widget_name, None)
            if widget_class is None:
                return QWidget(parent) # type: ignore
                #raise ValueError(f"No content widget for button type {type(data).__name__}")
            return widget_class(data, parent)

    class _ButtonOffContentWidget(_ContentWidget):
        '''Widget to show the content of a button that is off.'''
        def __init__(self, data: ButtonOff, parent: QWidget | None = None) -> None:
            super().__init__(parent)
            assert data.button_type == ButtonOff

    class _ButtonMouseButtonContentWidget(_ContentWidget):
        '''Widget to show the content of a button that is a mouse button.'''
        def __init__(self, data: Button, parent: QWidget | None = None) -> None:
            super().__init__(parent)
            assert isinstance(data, ButtonMouseButton)
            self.data = data
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            self.button_combo = QComboBox()
            for button in ButtonMouseButton.Type:
                self.button_combo.addItem(button.name)
            self.button_combo.currentIndexChanged.connect(self._on_button_changed)
            layout.addWidget(self.button_combo)
            self._set_data(data)

        def _set_data(self, data: ButtonMouseButton) -> None:
            '''Set the button data to display.'''
            self.data = data
            self.button_combo.blockSignals(True)
            button = data.mouse_button_type
            index = list(ButtonMouseButton.Type).index(button)
            self.button_combo.setCurrentIndex(index)
            self.button_combo.blockSignals(False)

        def _on_button_changed(self, index: int) -> None:
            '''Handle the user changing the mouse button from the combo box.'''
            button = list(ButtonMouseButton.Type)[index]
            self.data.mouse_button_type = button
            self.data_changed.emit()

    class _ButtonMouseFunctionContentWidget(_ContentWidget):
        '''Widget to show the content of a button that is a mouse function.'''
        def __init__(self, data: Button, parent: QWidget | None = None) -> None:
            super().__init__(parent)
            assert isinstance(data, ButtonMouseFunction)
            self.data = data
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            self.button_combo = QComboBox()
            for button in ButtonMouseFunction.Type:
                self.button_combo.addItem(button.name)
            layout.addWidget(self.button_combo)
            self._set_data(data)

        def _set_data(self, data: ButtonMouseFunction) -> None:
            '''Set the button data to display.'''
            self.data = data
            self.button_combo.blockSignals(True)
            button = data.type
            index = list(ButtonMouseFunction.Type).index(button)
            self.button_combo.setCurrentIndex(index)
            self.button_combo.blockSignals(False)

        def _on_button_changed(self, index: int) -> None:
            '''Handle the user changing the mouse function from the combo box.'''
            button = list(ButtonMouseFunction.Type)[index]
            self.data.type = button
            self.data_changed.emit()

    class _ButtonKeyPressContentWidget(_ContentWidget):
        '''Widget to show the content of a button that is a key press.'''
        def __init__(self, data: Button, parent: QWidget | None = None) -> None:
            super().__init__(parent)
            assert isinstance(data, ButtonKeyPress)
            self.data = data
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            key_layout = QHBoxLayout()
            key_layout.addWidget(QLabel("Key:"))
            self.key_label = QLabel(data.key.name)
            self.key_label.setFrameStyle(QLabel.Shape.Panel | QLabel.Shadow.Sunken)
            self.key_label.setStyleSheet("font-family: monospace;")
            key_layout.addWidget(self.key_label)
            key_layout.addStretch(1)
            layout.addLayout(key_layout)
            modifiers_layout = QGridLayout()
            self.modifier_checkboxes: dict[Modifier, QCheckBox] = {}
            for i, modifier in enumerate(Modifier):
                checkbox = QCheckBox(modifier.name)
                checkbox.stateChanged.connect(self._on_modifiers_changed)
                modifiers_layout.addWidget(checkbox, i % 4, i // 4)
                self.modifier_checkboxes[modifier] = checkbox
            layout.addLayout(modifiers_layout)
            self._set_data(data)

        def _set_data(self, data: ButtonKeyPress) -> None:
            '''Set the button data to display.'''
            self.data = data
            self.key_label.setText(data.key.name)
            for modifier, checkbox in self.modifier_checkboxes.items():
                checkbox.blockSignals(True)
                checkbox.setChecked(modifier in data.modifiers)
                checkbox.blockSignals(False)

        def _on_modifiers_changed(self) -> None:
            '''Handle the user changing the modifiers from the checkboxes.'''
            modifiers: set[Modifier] = set()
            for modifier, checkbox in self.modifier_checkboxes.items():
                if checkbox.isChecked():
                    modifiers.add(modifier)
            self.data.modifiers = modifiers
            self.data_changed.emit()

    class _ButtonSpecialKeyContentWidget(_ContentWidget):
        '''Widget to show the content of a button that is a special key.'''
        def __init__(self, data: ButtonSpecialKey, parent: QWidget | None = None) -> None:
            super().__init__(parent)
            assert isinstance(data, ButtonSpecialKey)
            self.data = data
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            self.type_combo = QComboBox()
            for key in ButtonSpecialKey.Type:
                self.type_combo.addItem(key.name)
            layout.addWidget(self.type_combo)
            self.type_combo.currentIndexChanged.connect(self._on_type_changed)
            self._set_data(data)

        def _set_data(self, data: ButtonSpecialKey) -> None:
            '''Set the button data to display.'''
            self.data = data
            index = list(ButtonSpecialKey.Type).index(data.type)
            self.type_combo.setCurrentIndex(index)

        def _on_type_changed(self, index: int) -> None:
            '''Handle the user changing the special key type from the combo box.'''
            key_type = list(ButtonSpecialKey.Type)[index]
            self.data.type = key_type
            self.data_changed.emit()

    class _ButtonMacroContentWidget(_ContentWidget):
        '''Widget to show the content of a button that is a macro.'''
        def __init__(self, data: ButtonMacro, parent: QWidget | None = None) -> None:
            super().__init__(parent)
            assert isinstance(data, ButtonMacro)
            self.data = data
            layout = QGridLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            self.macro_id_combo = QComboBox()
            for macro_id in range(1, ButtonMacro.MACRO_COUNT + 1):
                self.macro_id_combo.addItem(f'Macro {macro_id}')
            layout.addWidget(self.macro_id_combo, 0, 0, 1, 2)
            self.macro_id_combo.currentIndexChanged.connect(self._on_value_changed)
            self._repeat_radio = QRadioButton("Repeat")
            layout.addWidget(self._repeat_radio, 1, 0)
            self._repeat_radio.toggled.connect(self._on_value_changed)
            self._repeat_count_spinner = QSpinBox()
            self._repeat_count_spinner.setRange(1, ButtonMacro.MAX_REPEAT)
            layout.addWidget(self._repeat_count_spinner, 1, 1)
            self._repeat_count_spinner.valueChanged.connect(self._on_value_changed)
            self._hold_radio = QRadioButton("Hold")
            layout.addWidget(self._hold_radio, 2, 0)
            self._hold_radio.toggled.connect(self._on_value_changed)
            self._toggle_radio = QRadioButton("Toggle")
            layout.addWidget(self._toggle_radio, 3, 0)
            self._toggle_radio.toggled.connect(self._on_value_changed)
            self._set_data(data)

        def _set_data(self, data: ButtonMacro) -> None:
            '''Set the button data to display.'''
            self.data = data
            self.macro_id_combo.blockSignals(True)
            self._repeat_radio.blockSignals(True)
            self._repeat_count_spinner.blockSignals(True)
            self._toggle_radio.blockSignals(True)
            self._hold_radio.blockSignals(True)
            self.macro_id_combo.setCurrentIndex(data.macro_id - 1)
            if data.type == ButtonMacro.Type.REPEAT:
                self._repeat_radio.setChecked(True)
                self._repeat_count_spinner.setValue(data.repeat_count)
                self._repeat_count_spinner.setEnabled(True)
            elif data.type == ButtonMacro.Type.HOLD:
                self._hold_radio.setChecked(True)
                self._repeat_count_spinner.setEnabled(False)
            elif data.type == ButtonMacro.Type.TOGGLE:
                self._toggle_radio.setChecked(True)
                self._repeat_count_spinner.setEnabled(False)
            self.macro_id_combo.blockSignals(False)
            self._repeat_radio.blockSignals(False)
            self._repeat_count_spinner.blockSignals(False)
            self._toggle_radio.blockSignals(False)
            self._hold_radio.blockSignals(False)

        def _on_value_changed(self) -> None:
            '''Handle the user changing any value'''

            value = ButtonMacro(None)
            value.macro_id = self.macro_id_combo.currentIndex() + 1
            if self._repeat_radio.isChecked():
                value.type = ButtonMacro.Type.REPEAT
                value.repeat_count = self._repeat_count_spinner.value()
            elif self._hold_radio.isChecked():
                value.type = ButtonMacro.Type.HOLD
            elif self._toggle_radio.isChecked():
                value.type = ButtonMacro.Type.TOGGLE

            if value != self.data:
                self.data.macro_id = value.macro_id
                self.data.type = value.type
                self.data.repeat_count = value.repeat_count
                self.data_changed.emit()

    class _ButtonSniperContentWidget(_ContentWidget):
        '''Widget to show the content of a button that is a sniper button.'''
        def __init__(self, data: ButtonSniper, parent: QWidget | None = None) -> None:
            super().__init__(parent)
            assert isinstance(data, ButtonSniper)
            self.data = data
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            self.dpi_slider = QSlider(Qt.Orientation.Horizontal)
            self.dpi_slider.setRange(1, 100)
            layout.addWidget(self.dpi_slider)

        def _set_data(self, data: ButtonSniper) -> None:
            '''Set the button data to display.'''
            self.data = data
            # Todo: Set the slider value to the sniper sensitivity

        def _on_sensitivity_changed(self, value: int) -> None:
            '''Handle the user changing the sensitivity from the spinner.'''
            self.data_changed.emit()
            # Todo: Set the sniper sensitivity to the slider value

    class _ButtonFireKeyContentWidget(_ContentWidget):
        '''Widget to show the content of a button that is a fire key.'''
        def __init__(self, data: ButtonFireKey, parent: QWidget | None = None) -> None:
            super().__init__(parent)
            assert isinstance(data, ButtonFireKey)
            self.data = data
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            self.type_combo = QComboBox()
            self.type_combo.addItem("Mouse Button")
            self.type_combo.addItem("Keyboard")
            layout.addWidget(self.type_combo)

            self.mouse_button_combo = QComboBox()
            for button in ButtonMouseButton.Type:
                self.mouse_button_combo.addItem(button.name)
            layout.addWidget(self.mouse_button_combo)
            self.mouse_button_combo.currentIndexChanged.connect(self._on_value_changed)

            self.keyboard_key_label = QLabel(f'Key code: {data.key}')
            layout.addWidget(self.keyboard_key_label)


        def _set_data(self, data: ButtonFireKey) -> None:
            '''Set the button data to display.'''
            self.data = data
            if isinstance(data.key, ButtonMouseButton):
                self.type_combo.setCurrentIndex(0)
                self.mouse_button_combo.blockSignals(True)
                button = data.key.mouse_button_type
                index = list(ButtonMouseButton.Type).index(button)
                self.mouse_button_combo.setCurrentIndex(index)
                self.mouse_button_combo.blockSignals(False)
                self.mouse_button_combo.setVisible(True)
                self.keyboard_key_label.setVisible(False)
            elif isinstance(data.key, ButtonKeyPress):
                self.type_combo.setCurrentIndex(1)
                self.keyboard_key_label.setText(f'Key code: {data.key.key}')
                self.mouse_button_combo.setVisible(False)
                self.keyboard_key_label.setVisible(True)

        def _on_value_changed(self) -> None:
            '''Handle the user changing a value.'''
            self.data_changed.emit()

    class _ButtomCustomContentWidget(_ContentWidget):
        '''Widget to show the content of a button that is custom.'''
        def __init__(self, data: ButtomCustom, parent: QWidget | None = None) -> None:
            super().__init__(parent)
            assert isinstance(data, ButtomCustom)
            self.data = data
            layout = QGridLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(QLabel("Specify raw data. Advanced users only!"), 0, 0, 1, 5)
            self.spin_boxes: list[QSpinBox] = []
            self.hex_labels: list[QLabel] = []
            for i in range(4):
                spin_box = QSpinBox()
                spin_box.setRange(0, 255)
                layout.addWidget(spin_box, 1, i)
                spin_box.valueChanged.connect(self._on_value_changed)
                self.spin_boxes.append(spin_box)
                hex_label = QLabel("0x00")
                hex_label.setStyleSheet("font-family: monospace;")
                layout.addWidget(hex_label, 2, i)
                self.hex_labels.append(hex_label)
            layout.setColumnStretch(4, 1)

        def _set_data(self, data: ButtomCustom) -> None:
            '''Set the button data to display.'''
            self.data = data
            for i in range(4):
                self.spin_boxes[i].blockSignals(True)
                self.spin_boxes[i].setValue(data.data[i])
                self.spin_boxes[i].blockSignals(False)
                self.hex_labels[i].setText(f"0x{data.data[i]:02X}")

        def _on_value_changed(self) -> None:
            '''Handle the user changing the custom data.'''
            for i in range(4):
                self.data.data[i] = self.spin_boxes[i].value()
                self.hex_labels[i].setText(f"0x{self.data.data[i]:02X}")
            self.data_changed.emit()
