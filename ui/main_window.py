''' Main application window. '''
import logging
import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (QApplication, QComboBox, QHBoxLayout, QLabel,
                               QMainWindow, QPushButton, QSizePolicy,
                               QSplitter, QVBoxLayout, QWidget)

from ui.button_widget import ButtonWidget
from ui.downloader import download
from ui.mouse_config import mouse_configs
from ui.mouse_data import PROFILE_COUNT, MouseData, ProfileData
from ui.mouse_image import MouseImageWidget
from ui.mouse_selector_widget import MouseSelectorWidget
from ui.vertical_tab_wiget import HorizontalTabBar, VerticalTabWidget

logger = logging.getLogger(__name__)


ICON_SOURCE = "https://redragon.com/cdn/shop/files/small_logo.png?crop=left&height=64&width=64"


class MainWindow(QMainWindow):
    '''Main application window.'''

    def __init__(self) -> None:
        super().__init__()

        self.profile = 0
        self.mouse: MouseData | None = None
        self.mouse_config = mouse_configs[None]
        self.mouse_image: MouseImageWidget
        self.warning_label: QLabel
        self.mouse_widget: QWidget
        self.buttons_widget: VerticalTabWidget
        self.active_profile_label: QLabel

        self.setWindowTitle("M811 Configurator")
        self.resize(800, 600)
        download(ICON_SOURCE, self._set_app_icon)
        self._build_ui()
        self.mouse_selector.refresh_mice()

    def _build_ui(self) -> None:
        """Create and wire all widgets; called once from __init__."""
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
        mouse_widget_layout.addWidget(self._build_profile_bar())
        mouse_widget_layout.addWidget(self._build_splitter())

        layout.addWidget(self.mouse_widget)
        self.setCentralWidget(central_widget)

    def _build_profile_bar(self) -> QWidget:
        """Build the profile-selector / upload / discard bar."""
        profile_widget = QWidget()
        profile_widget_layout = QHBoxLayout(profile_widget)
        profile_widget_layout.setContentsMargins(0, 0, 0, 0)

        profiles_combo = QComboBox()
        for i in range(PROFILE_COUNT):
            profiles_combo.addItem(f"Profile {i+1}")
        profiles_combo.currentIndexChanged.connect(self._select_profile)
        profile_widget_layout.addWidget(profiles_combo)

        profile_widget_layout.addWidget(QLabel("Active Profile:"))
        self.active_profile_label = QLabel("❓")
        profile_widget_layout.addWidget(self.active_profile_label)

        profile_widget_layout.addStretch(1)

        upload_button = QPushButton("Upload Changes")
        upload_button.setEnabled(False)
        profile_widget_layout.addWidget(upload_button)

        discard_button = QPushButton("Discard Changes")
        discard_button.setEnabled(False)
        profile_widget_layout.addWidget(discard_button)

        return profile_widget

    def _build_splitter(self) -> QSplitter:
        """Build the horizontal splitter containing the mouse image and button tabs."""
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
        self.buttons_widget = VerticalTabWidget()
        self.buttons_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.buttons_widget.currentChanged.connect(self._on_button_selected)
        splitter_right_layout.addWidget(self.buttons_widget)
        splitter.addWidget(splitter_right)
        splitter.setStretchFactor(1, 1)

        return splitter

    def _on_mouse_selected(self, mouse: MouseData | None, name: str | None) -> None:
        self.mouse = mouse
        logger.debug("Selected mouse: %s", name if name is not None else "None")
        mouse_type = mouse.mouse_type if mouse is not None else None
        self.mouse_config = mouse_configs.get(mouse_type, mouse_configs[None])

        if mouse:
            self.mouse_image.load_svg(self.mouse_config.image)
            self._start_poll_active_profile()
        else:
            self._stop_poll_active_profile()
            pixmap = QPixmap(400, 300)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            painter.setPen(QColor("red"))
            painter.setFont(QFont("Arial", 32))
            painter.drawText(
                pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "No mouse selected")
            painter.end()
            self.mouse_image.setPixmap(pixmap)

        if mouse and mouse.status != MouseData.Status.NO_ACCESS:
            if not self.mouse_config.fully_supported:
                self.warning_label.setText(MainWindow._create_unsupported_warning_text())
                self.warning_label.setVisible(True)
            else:
                self.warning_label.setVisible(False)
            self.mouse_widget.setEnabled(True)
            self._read_mouse()
        elif mouse and mouse.status == MouseData.Status.NO_ACCESS:
            self.mouse = None
            self.warning_label.setText(
                self._create_inaccessible_warning_text(mouse))
            self.warning_label.setVisible(True)
            self.mouse_widget.setEnabled(False)
        else:
            self.mouse = None
            self.warning_label.setVisible(False)
            self.mouse_widget.setEnabled(False)

    def _select_profile(self, index: int) -> None:
        logger.debug("Selected profile: %d", index + 1)
        self.profile = index
        self._read_mouse()

    def _read_mouse(self) -> None:
        if self.mouse is None:
            return

        self.mouse.load_from_mouse()

        self.buttons_widget.clear()
        for button_index, button in enumerate(self.mouse.get_profile_data(self.profile).buttons()):
            button_name = self.mouse_config.buttons[button_index] if button_index < len(
                self.mouse_config.buttons) else f"Button {button_index+1}"
            button_widget = ButtonWidget(button)
            self.buttons_widget.addTab(button_widget, button_name)

    def _set_app_icon(self, data: bytes | Exception) -> None:
        if isinstance(data, Exception):
            logger.error("Failed to download application icon: %s", data)
            return

        app_icon = QPixmap()
        if not app_icon.loadFromData(data):
            logger.error(
                "Failed to load application icon from downloaded data")
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
        tab_bar.set_hovered_tab(button_index)

    def _start_poll_active_profile(self):
        self._stop_poll_active_profile()
        logger.debug("Starting active profile polling")
        self.active_profile_timer = QTimer(self)
        self.active_profile_timer.timeout.connect(self._poll_active_profile)
        self.active_profile_timer.start(200)

    def _stop_poll_active_profile(self):
        if hasattr(self, 'active_profile_timer'):
            logger.debug("Stopping active profile polling")
            self.active_profile_timer.stop()
            del self.active_profile_timer

    def _poll_active_profile(self):
        if self.mouse is None:
            self.active_profile_label.setText("❓")
            return

        active_profile = self.mouse.load_active_profile()
        ICONS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
        self.active_profile_label.setText(ICONS[active_profile])

    @staticmethod
    def _create_inaccessible_warning_text(mouse: MouseData) -> str:
        # pylint: disable=line-too-long
        return f"Selected mouse is not accessible. Please check permissions of <span style='font-family: monospace;'>/dev/bus/usb/{mouse.usb_path[0]:03d}/{mouse.usb_path[1]:03d}</span>.<br>\n" \
            f"To grant access, you can create a udev rule like this in e.g. <span style='font-family: monospace;'>/etc/udev/rules.d/99-mouse.rules</span>:<br>\n" \
            f"<span style='font-family: monospace;'>SUBSYSTEM==\"usb\", ATTRS{{idVendor}}==\"{mouse.usb_id[0]:04x}\", ATTRS{{idProduct}}==\"{mouse.usb_id[1]:04x}\", MODE=\"0666\"</span><br>\n" \
            f"After creating the rule, reload udev rules with <span style='font-family: monospace;'>sudo udevadm control --reload</span> and re-plug the mouse."

    @staticmethod
    def _create_unsupported_warning_text() -> str:
        # pylint: disable=line-too-long
        return "This mouse model is not fully supported. Some features may not work correctly.<br>\n" \
               "You can raise an issue on GitHub: <a href='https://github.com/Mr-Clear/M811-Configurator' style='font-family: monospace;'>https://github.com/Mr-Clear/M811-Configurator</a>."



def start_app() -> int:
    '''Creates the main window and starts the application event loop.'''
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()
