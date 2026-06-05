'''Provides a widget for selecting a mouse from the list of connected USB devices.'''

import logging

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QComboBox, QHBoxLayout, QLabel, QPushButton,
                               QWidget)

from mouse import Mouse, UsbDevice

logger = logging.getLogger(__name__)


class MouseSelectorWidget(QWidget):
    '''Widget for selecting a mouse from the list of connected USB devices.'''
    mouse_selected = Signal(UsbDevice)
    mouse_deselected = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self.mouse: Mouse | None = None
        self.mice: list[UsbDevice] = []
        self.selected_mouse_index = -1

        layout = QHBoxLayout(self)
        self.select_mouse_combo = QComboBox()
        self.select_mouse_combo.currentIndexChanged.connect(
            self._select_mouse_by_index)
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_mice)
        layout.addWidget(QLabel("Select mouse:"))
        layout.addWidget(self.select_mouse_combo, 1)
        layout.addWidget(refresh_button)

    @property
    def current_usb_device(self) -> UsbDevice | None:
        '''Returns the currently selected mouse's UsbDevice, or None if no mouse is selected.'''
        return self.mice[self.selected_mouse_index] \
            if self.selected_mouse_index >= 0 and self.selected_mouse_index < len(self.mice) \
            else None

    def refresh_mice(self):
        '''Refresh the list of connected mice and update the combo box.'''
        current_device = self.current_usb_device

        self.mice = Mouse.find_devices()
        logger.info("Found %d mice: %s", len(self.mice), [mouse.name for mouse in self.mice])
        self.select_mouse_combo.blockSignals(True)
        self.select_mouse_combo.clear()

        if not self.mice:
            self.select_mouse_combo.addItem("No mice found")
            self.select_mouse_combo.setEnabled(False)
            self.mouse = None
        else:
            self.select_mouse_combo.setEnabled(True)

        for index, mouse in enumerate(self.mice):
            label = mouse.name or f"Device {mouse.dev.idProduct:04x}"
            if not mouse.access:
                label = f"{label} (inaccessible)"
            self.select_mouse_combo.addItem(label)
            if not mouse.access:
                self.select_mouse_combo.setItemData(
                    index, QColor("red"), Qt.ItemDataRole.ForegroundRole)

        if current_device is not None:
            for index, mouse in enumerate(self.mice):
                if mouse.dev == current_device.dev:
                    self.select_mouse_combo.setCurrentIndex(index)
                    break

        if not self.mice:
            self.mouse_deselected.emit()
        if not self.current_usb_device and self.mice:
            logger.debug(
                "No previously selected mouse found, selecting first available mouse.")
            self.select_mouse_combo.setCurrentIndex(0)
            self._select_mouse_by_index(0)

        self.select_mouse_combo.blockSignals(False)

    def _select_mouse_by_index(self, index: int) -> None:
        if index < 0 or index >= len(self.mice):
            self.mouse_deselected.emit()
        else:
            self.mouse_selected.emit(self.mice[index])
