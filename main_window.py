import sys
from dataclasses import dataclass
from urllib.request import urlopen

from PySide6.QtCore import Qt
from PySide6.QtGui import (QBrush, QColor, QFont, QIcon, QPainter, QPen,
                           QPixmap, QPolygon)
from PySide6.QtWidgets import (QApplication, QComboBox, QFormLayout,
                               QHBoxLayout, QLabel, QMainWindow, QPushButton,
                               QScrollArea, QSizePolicy, QSplitter, QTabWidget,
                               QVBoxLayout, QWidget)
from usb.core import USBError

from button_widget import ButtonWidget
from downloader import download
from mouse import PROFILE_COUNT, Mouse, MouseType, UsbDevice
from vertical_tab_wiget import VerticalTabWidget

icon_source = "https://redragon.com/cdn/shop/files/small_logo.png?crop=left&height=64&width=64"

@dataclass
class MouseConfig:
    image_source: str
    buttons: list[str]
    button_areas: list[QPolygon] | None = None
    fully_supported: bool = True


mouse_configs: dict[MouseType | None, MouseConfig] = {
    MouseType.M811: MouseConfig(
        image_source="https://redragonshop.com/cdn/shop/products/MMOGamingMouse_2.png",
        buttons = ['LMB', 'RMB', 'MMB', 'Forward', 'Backward', 'DPI+', 'DPI-', '?', '1', '2', '3', '4', '5', '6', '7', '8'],
    ),
    None: MouseConfig(
        image_source="https://redragon.com/cdn/shop/files/small_logo.png",
        buttons = [str(i) for i in range(1, 20)],
        fully_supported=False,
    ),
}


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.selected_mouse_index = -1
        self.profile = 0

        self.setWindowTitle("M811 Configurator")
        self.resize(800, 600)
        self.mouse: Mouse | None = None
        self.mice: list[UsbDevice] = []

        central_widget = QWidget(self)
        layout = QVBoxLayout(central_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        controls_layout = QHBoxLayout()
        self.select_mouse_combo = QComboBox()
        self.select_mouse_combo.currentIndexChanged.connect(self._select_mouse_by_index)
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self._load_mice)
        controls_layout.addWidget(QLabel("Select mouse:"))
        controls_layout.addWidget(self.select_mouse_combo, 1)
        controls_layout.addWidget(refresh_button)
        layout.addLayout(controls_layout)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)

        self.warning_label = QLabel()
        self.warning_label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        self.warning_label.setStyleSheet("color: red;")
        self.warning_label.setVisible(False)
        self.warning_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.warning_label)

        self.mouse_widget = QWidget()
        self.mouse_widget.setLayout(QVBoxLayout())
        self.mouse_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.mouse_widget.layout().setContentsMargins(0, 0, 0, 0)

        self.profile_widget = QWidget()
        self.profile_widget.setLayout(QHBoxLayout())
        self.profile_widget.layout().setContentsMargins(0, 0, 0, 0)
        self.mouse_widget.layout().addWidget(self.profile_widget)

        self.profiles_combo = QComboBox()
        for i in range(PROFILE_COUNT):
            self.profiles_combo.addItem(f"Profile {i+1}")
        self.profiles_combo.currentIndexChanged.connect(self._select_profile)
        self.profile_widget.layout().addWidget(self.profiles_combo)

        self.upload_button = QPushButton("Upload Changes")
        self.upload_button.setEnabled(False)
        self.profile_widget.layout().addWidget(self.upload_button)

        self.discard_button = QPushButton("Discard Changes")
        self.discard_button.setEnabled(False)
        self.profile_widget.layout().addWidget(self.discard_button)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        splitter_left = QWidget()
        splitter_left.setLayout(QVBoxLayout())
        splitter_left.layout().setAlignment(Qt.AlignmentFlag.AlignTop)
        splitter_left.layout().setContentsMargins(0, 0, 0, 0)
        splitter_left.layout().addWidget(self.image_label)
        splitter.addWidget(splitter_left)
        splitter.setStretchFactor(0, 0)

        splitter_right = QWidget()
        splitter_right.setLayout(QVBoxLayout())
        splitter_right.layout().setAlignment(Qt.AlignmentFlag.AlignTop)
        splitter_right.layout().setContentsMargins(0, 0, 0, 0)
        splitter.addWidget(splitter_right)
        splitter.setStretchFactor(1, 1)

        self.buttons_widget = VerticalTabWidget()
        self.buttons_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        splitter_right.layout().addWidget(self.buttons_widget)

        self.mouse_widget.layout().addWidget(splitter)
        layout.addWidget(self.mouse_widget)
        self.setCentralWidget(central_widget)

        self._load_mice()

        download(icon_source, self._set_app_icon)

    @property
    def current_usb_device(self) -> UsbDevice | None:
        return self.mice[self.selected_mouse_index] if self.selected_mouse_index >= 0 and self.selected_mouse_index < len(self.mice) else None

    def _load_mice(self):
        current_device = self.current_usb_device

        self.mice = Mouse.find_devices()
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
                self.select_mouse_combo.setItemData(index, QColor("red"), Qt.ItemDataRole.ForegroundRole)

        if current_device is not None:
            for index, mouse in enumerate(self.mice):
                if mouse.dev == current_device.dev:
                    self.select_mouse_combo.setCurrentIndex(index)
                    break

        print(f"Selected mouse: {self.current_usb_device}, Mice count: {len(self.mice)}")
        if not self.mice:
            self._select_mouse(None)
        if not self.current_usb_device and self.mice:
            print("No previously selected mouse found, selecting first available mouse.")
            self.select_mouse_combo.setCurrentIndex(0)
            self._select_mouse_by_index(0)

        self.select_mouse_combo.blockSignals(False)


    def _select_mouse_by_index(self, index: int) -> None:
        if index < 0 or index >= len(self.mice):
            self._select_mouse(None)
        else:
            self._select_mouse(self.mice[index])

    def _select_mouse(self, mouse: UsbDevice) -> None:
        print(f"Selected mouse: {mouse.name if mouse is not None else 'None'}")
        type = mouse.type if mouse is not None else None
        self.mouse_config = mouse_configs.get(type, mouse_configs[None])

        if mouse:
            download(self.mouse_config.image_source, self._set_image)
        else:
            pixmap = QPixmap(400, 300)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            painter.setPen(QColor("red"))
            painter.setFont(QFont("Arial", 32))
            painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "No mouse selected")
            painter.end()
            self.image_label.setPixmap(pixmap)

        if mouse and mouse.access:
            self.mouse = Mouse.from_device(mouse.dev)
            if not self.mouse_config.fully_supported:
                self.warning_label.setText("This mouse model is not fully supported. Some features may not work correctly.<br>\n" \
                                           "You can raise an issue on GitHub: <a href='https://github.com/Mr-Clear/M811-Configurator' style='font-family: monospace;'>https://github.com/Mr-Clear/M811-Configurator</a>.")
                self.warning_label.setVisible(True)
                self.mouse_widget.setEnabled(False)
            else:
                self.warning_label.setVisible(False)
                self.mouse_widget.setEnabled(True)
            self._read_mouse()
        elif mouse and not mouse.access:
            self.mouse = None
            self.warning_label.setText(self.create_inaccessible_warning_text(mouse))
            self.warning_label.setVisible(True)
            self.mouse_widget.setEnabled(False)
        else:
            self.mouse = None
            self.warning_label.setVisible(False)
            self.mouse_widget.setEnabled(False)

    def _select_profile(self, index: int) -> None:
        print(f"Selected profile: {index}")
        self.profile = index
        self._read_mouse()

    def _set_image(self, data: bytes | Exception) -> None:
        if isinstance(data, Exception):
            print(f"Failed to download image: {data}")
            return

        pixmap = QPixmap()
        if not pixmap.loadFromData(data):
            print("Failed to load image from downloaded data")
            return

        pixmap = pixmap.scaledToWidth(400, Qt.TransformationMode.SmoothTransformation)
        self.image_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.image_label.setFixedSize(pixmap.size())
        self.image_label.setPixmap(pixmap)

    def _unregister_mouse(self) -> None:
        if self.mouse is None:
            return
        try:
            self.mouse.dev.detach_kernel_driver(2)
        except USBError:
            pass

    def _register_mouse(self) -> None:
        if self.mouse is None:
            return
        try:
            self.mouse.dev.attach_kernel_driver(2)
        except USBError:
            pass

    def _read_mouse(self) -> None:
        if self.mouse is None:
            return

        keymap = self.mouse.get_keymap(self.profile, len(self.mouse_config.buttons))
        self.buttons_widget.clear()
        for button_index, keys in enumerate(keymap):
            button_name = self.mouse_config.buttons[button_index] if button_index < len(self.mouse_config.buttons) else f"Button {button_index+1}"
            button_widget = ButtonWidget(keys)
            self.buttons_widget.addTab(button_widget, button_name)

    def closeEvent(self, event) -> None:
        self._register_mouse()
        super().closeEvent(event)

    def _set_app_icon(self, data: bytes | Exception) -> None:
        if isinstance(data, Exception):
            print(f"Failed to download application icon: {data}")
            return

        app_icon = QPixmap()
        if not app_icon.loadFromData(data):
            print("Failed to load application icon from downloaded data")
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
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.drawPixmap(0, 0, app_icon)
        painter.end()
        self.setWindowIcon(QIcon(circled_icon))

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
