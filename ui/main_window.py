import logging
import sys

from ui.mouse_selector_widget import MouseSelectorWidget

logger = logging.getLogger(__name__)

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (QApplication, QComboBox, QHBoxLayout, QLabel,
                               QMainWindow, QPushButton, QSizePolicy,
                               QSplitter, QVBoxLayout, QWidget)

from mouse import PROFILE_COUNT, Mouse, UsbDevice
from ui.button_widget import ButtonWidget
from ui.downloader import download
from ui.mouse_config import mouse_configs
from ui.mouse_image import MouseImageWidget
from ui.vertical_tab_wiget import HorizontalTabBar, VerticalTabWidget

icon_source = "https://redragon.com/cdn/shop/files/small_logo.png?crop=left&height=64&width=64"


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.profile = 0

        self.setWindowTitle("M811 Configurator")
        self.resize(800, 600)
        download(icon_source, self._set_app_icon)

        central_widget = QWidget(self)
        layout = QVBoxLayout(central_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.mouse_selector = MouseSelectorWidget()
        self.mouse_selector.mouse_selected.connect(self._on_mouse_selected)
        self.mouse_selector.mouse_deselected.connect(self._on_mouse_selected)
        layout.addWidget(self.mouse_selector)

        self.mouse_image = MouseImageWidget()
        self.mouse_image.fixed_width = 400
        self.mouse_image.button_clicked.connect(self._on_button_clicked)
        self.mouse_image.button_hovered.connect(self._on_button_hovered)

        self.warning_label = QLabel()
        self.warning_label.setAlignment(
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        self.warning_label.setStyleSheet("color: red;")
        self.warning_label.setVisible(False)
        self.warning_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.warning_label)

        self.mouse_widget = QWidget()
        mouse_widget_layout = QVBoxLayout(self.mouse_widget)
        self.mouse_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        mouse_widget_layout.setContentsMargins(0, 0, 0, 0)

        self.profile_widget = QWidget()
        profile_widget_layout = QHBoxLayout(self.profile_widget)
        profile_widget_layout.setContentsMargins(0, 0, 0, 0)
        mouse_widget_layout.addWidget(self.profile_widget)

        self.profiles_combo = QComboBox()
        for i in range(PROFILE_COUNT):
            self.profiles_combo.addItem(f"Profile {i+1}")
        self.profiles_combo.currentIndexChanged.connect(self._select_profile)
        profile_widget_layout.addWidget(self.profiles_combo)

        self.upload_button = QPushButton("Upload Changes")
        self.upload_button.setEnabled(False)
        profile_widget_layout.addWidget(self.upload_button)

        self.discard_button = QPushButton("Discard Changes")
        self.discard_button.setEnabled(False)
        profile_widget_layout.addWidget(self.discard_button)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setSizePolicy(QSizePolicy.Policy.Expanding,
                               QSizePolicy.Policy.Expanding)
        splitter_left = QWidget()
        splitter_left_layout = QVBoxLayout(splitter_left)
        splitter_left_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        splitter_left_layout.setContentsMargins(0, 0, 0, 0)
        splitter_left_layout.addWidget(self.mouse_image)
        splitter.addWidget(splitter_left)
        splitter.setStretchFactor(0, 0)

        splitter_right = QWidget()
        splitter_right_layout = QVBoxLayout(splitter_right)
        splitter_right_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        splitter_right_layout.setContentsMargins(0, 0, 0, 0)
        splitter.addWidget(splitter_right)
        splitter.setStretchFactor(1, 1)

        self.buttons_widget = VerticalTabWidget()
        self.buttons_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.buttons_widget.currentChanged.connect(self._on_button_selected)
        splitter_right_layout.addWidget(self.buttons_widget)

        mouse_widget_layout.addWidget(splitter)
        layout.addWidget(self.mouse_widget)
        self.setCentralWidget(central_widget)

        self.mouse_selector.refresh_mice()

    def _on_mouse_selected(self, mouse: UsbDevice | None = None) -> None:
        logger.debug(f"Selected mouse: {mouse.name if mouse is not None else None}")
        type = mouse.type if mouse is not None else None
        self.mouse_config = mouse_configs.get(type, mouse_configs[None])

        if mouse:
            self.mouse_image.load_svg(self.mouse_config.image)
        else:
            pixmap = QPixmap(400, 300)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            painter.setPen(QColor("red"))
            painter.setFont(QFont("Arial", 32))
            painter.drawText(
                pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "No mouse selected")
            painter.end()
            self.mouse_image.setPixmap(pixmap)

        if mouse and mouse.access:
            self.mouse = Mouse.from_device(mouse.dev)
            if not self.mouse_config.fully_supported:
                self.warning_label.setText("This mouse model is not fully supported. Some features may not work correctly.<br>\n"
                                           "You can raise an issue on GitHub: <a href='https://github.com/Mr-Clear/M811-Configurator' style='font-family: monospace;'>https://github.com/Mr-Clear/M811-Configurator</a>.")
                self.warning_label.setVisible(True)
            else:
                self.warning_label.setVisible(False)
            self.mouse_widget.setEnabled(True)
            self._read_mouse()
        elif mouse and not mouse.access:
            self.mouse = None
            self.warning_label.setText(
                self.create_inaccessible_warning_text(mouse))
            self.warning_label.setVisible(True)
            self.mouse_widget.setEnabled(False)
        else:
            self.mouse = None
            self.warning_label.setVisible(False)
            self.mouse_widget.setEnabled(False)

    def _select_profile(self, index: int) -> None:
        logger.debug(f"Selected profile: {index + 1}")
        self.profile = index
        self._read_mouse()

    def _read_mouse(self) -> None:
        if self.mouse is None:
            return

        logger.info(f"Reading configuration from mouse {self.mouse.dev.idVendor:04x}:{self.mouse.dev.idProduct:04x} at /dev/bus/usb/{self.mouse.dev.bus:03d}/{self.mouse.dev.address:03d}")
        keymap = self.mouse.get_keymap(
            self.profile, len(self.mouse_config.buttons))
        self.buttons_widget.clear()
        for button_index, keys in enumerate(keymap):
            button_name = self.mouse_config.buttons[button_index] if button_index < len(
                self.mouse_config.buttons) else f"Button {button_index+1}"
            button_widget = ButtonWidget(keys)
            self.buttons_widget.addTab(button_widget, button_name)

    def _set_app_icon(self, data: bytes | Exception) -> None:
        if isinstance(data, Exception):
            logger.error("Failed to download application icon: %s", data)
            return

        app_icon = QPixmap()
        if not app_icon.loadFromData(data):
            logger.error("Failed to load application icon from downloaded data")
            return

        circled_icon = QPixmap(app_icon.size())
        circled_icon.fill(Qt.GlobalColor.transparent)
        painter = QPainter(circled_icon)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QColor("black"))
        painter.setBrush(QColor("white"))
        radius = app_icon.width() // 2
        center = app_icon.rect().center()
        painter.drawEllipse(center, radius, radius)
        painter.setCompositionMode(
            QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.drawPixmap(0, 0, app_icon)
        painter.end()
        self.setWindowIcon(QIcon(circled_icon))

    def _on_button_selected(self, button_index: int) -> None:
        self.mouse_image.set_selected_button(button_index)

    def _on_button_clicked(self, button_index: int) -> None:
        if 0 <= button_index < len(self.mouse_config.buttons):
            self.buttons_widget.setCurrentIndex(button_index)

    def _on_button_hovered(self, button_index: int) -> None:
        tab_bar = self.buttons_widget.tabBar()
        assert isinstance(tab_bar, HorizontalTabBar)
        tab_bar.setHoveredTab(button_index)

    @staticmethod
    def create_inaccessible_warning_text(dev: UsbDevice) -> str:
        return f"Selected mouse is not accessible. Please check permissions of <span style='font-family: monospace;'>/dev/bus/usb/{dev.dev.bus:03d}/{dev.dev.address:03d}</span>.<br>\n" \
            f"To grant access, you can create a udev rule like this in e.g. <span style='font-family: monospace;'>/etc/udev/rules.d/99-mouse.rules</span>:<br>\n" \
            f"<span style='font-family: monospace;'>SUBSYSTEM==\"usb\", ATTRS{{idVendor}}==\"{dev.dev.idVendor:04x}\", ATTRS{{idProduct}}==\"{dev.dev.idProduct:04x}\", MODE=\"0666\"</span><br>\n" \
            f"After creating the rule, reload udev rules with <span style='font-family: monospace;'>sudo udevadm control --reload</span> and re-plug the mouse."


def start_app() -> int:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()
