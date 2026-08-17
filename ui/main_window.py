''' Main application window. '''
import logging
import os
import sys

from PySide6.QtCore import QRunnable, Qt, QThreadPool, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (QApplication, QComboBox, QHBoxLayout, QLabel,
                               QMainWindow, QPushButton, QSizePolicy,
                               QSplitter, QVBoxLayout, QWidget)

from mouse_data import MouseData
from mouse_data.mouse import Mouse
from mouse_data.mouse_definition import MouseDefinition
from ui.buttons_widget import ButtonsWidget
from ui.downloader import download
from ui.mouse_image import MouseImageWidget
from ui.mouse_selector_widget import MouseSelectorWidget
from ui.usb_connection import UsbConnection

logger = logging.getLogger(__name__)


ICON_SOURCE = "https://redragon.com/cdn/shop/files/small_logo.png?crop=left&height=64&width=64"


class MainWindow(QMainWindow):
    '''Main application window.'''
    data_loaded_from_mouse: Signal = Signal()

    def __init__(self) -> None:
        super().__init__()

        self.mode = 0
        self.mouse: Mouse | None = None
        self.mouse_image: MouseImageWidget
        self.mouse_widget: QWidget
        self.buttons_widget: ButtonsWidget
        self.active_mode_label: QLabel

        self.setWindowTitle("M811 Configurator")
        self.resize(800, 600)
        download(ICON_SOURCE, self._set_app_icon)
        self._build_ui()

        self.data_loaded_from_mouse.connect(self._read_mouse)

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

        self.mouse_widget = QWidget()
        mouse_widget_layout = QVBoxLayout(self.mouse_widget)
        self.mouse_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        mouse_widget_layout.setContentsMargins(0, 0, 0, 0)
        mouse_widget_layout.addWidget(self._build_mode_bar())
        mouse_widget_layout.addWidget(self._build_splitter())

        layout.addWidget(self.mouse_widget)
        self.setCentralWidget(central_widget)

    def _build_mode_bar(self) -> QWidget:
        """Build the mode-selector / upload / discard bar."""
        mode_widget = QWidget()
        mode_widget_layout = QHBoxLayout(mode_widget)
        mode_widget_layout.setContentsMargins(0, 0, 0, 0)

        modes_combo = QComboBox()
        for i in range(MouseData.MODE_COUNT):
            modes_combo.addItem(f"Mode {i+1}")
        modes_combo.currentIndexChanged.connect(self._select_mode)
        mode_widget_layout.addWidget(modes_combo)

        mode_widget_layout.addWidget(QLabel("Active Mode:"))
        self.active_mode_label = QLabel("❓")
        mode_widget_layout.addWidget(self.active_mode_label)

        mode_widget_layout.addStretch(1)

        upload_button = QPushButton("Upload Changes")
        upload_button.setEnabled(False)
        mode_widget_layout.addWidget(upload_button)

        discard_button = QPushButton("Discard Changes")
        discard_button.setEnabled(False)
        mode_widget_layout.addWidget(discard_button)

        return mode_widget

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
        self.buttons_widget = ButtonsWidget()
        self.buttons_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.buttons_widget.selected_button_changed.connect(self._on_button_selected)
        splitter_right_layout.addWidget(self.buttons_widget)
        splitter.addWidget(splitter_right)
        splitter.setStretchFactor(1, 1)

        return splitter

    def _on_mouse_selected(self, connection: UsbConnection | None) -> None:
        if connection:
            definition = MouseDefinition.from_device(connection.dev.idVendor, connection.dev.idProduct)
            mouse_data = MouseData(definition.data_definition, definition.memory_size)
            self.mouse = Mouse(definition, mouse_data, connection)
            logger.info("Selected mouse: %s (%s, %s, %s)", definition.name, connection.name, connection.ids, connection.path)

            self.mouse_image.load_svg(definition.image)
            self._start_poll_active_mode()
            self.mouse_widget.setEnabled(True)

            self._load_mouse_data()
        else:
            self.mouse = None
            self._stop_poll_active_mode()
            pixmap = QPixmap(400, 300)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            painter.setPen(QColor("red"))
            painter.setFont(QFont("Arial", 32))
            painter.drawText(
                pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "No mouse selected")
            painter.end()
            self.mouse_image.setPixmap(pixmap)
            self.mouse_widget.setEnabled(False)

    def _select_mode(self, index: int) -> None:
        logger.debug("Selected mode: %d", index + 1)
        self.mode = index
        self.buttons_widget.set_selected_mode_index(index)

    def _read_mouse(self) -> None:
        if self.mouse is None:
            return

        self.buttons_widget.set_data(self.mouse.data, self.mouse.definition)

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
        if self.mouse is not None:
            if 0 <= button_index < len(self.mouse.definition.buttons):
                self.buttons_widget.set_selected_button_index(button_index)

    def _on_button_hovered(self, button_index: int) -> None:
        self.buttons_widget.set_hovered_button_index(button_index)

    def _start_poll_active_mode(self):
        self._stop_poll_active_mode()
        logger.debug("Starting active mode polling")
        self.active_mode_timer = QTimer(self)
        self.active_mode_timer.timeout.connect(self._poll_active_mode)
        self.active_mode_timer.start(200)

    def _stop_poll_active_mode(self):
        if hasattr(self, 'active_mode_timer'):
            logger.debug("Stopping active mode polling")
            self.active_mode_timer.stop()
            del self.active_mode_timer

    def _poll_active_mode(self):
        if self.mouse is None:
            self.active_mode_label.setText("❓")
            return

        #active_mode = self.mouse.load_active_mode()
        #ICONS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
        #self.active_mode_label.setText(ICONS[active_mode])

    def _load_mouse_data(self, reload_from_mouse: bool = False):
        if self.mouse is None:
            return

        cache_file_name = f'.cache/mouse_data_{self.mouse.definition.name}_{self.mouse.connection.ids}_{self.mouse.connection.path}.dump'
        if os.path.exists(cache_file_name) and not reload_from_mouse:
            try:
                with open(cache_file_name, 'rb') as f:
                    self.mouse.data_on_device = f.read()
            except Exception as e:
                logger.error("Failed to load mouse data from cache: %s", e)
                os.remove(cache_file_name)
            if self.mouse.data_on_device is not None:
                self.mouse.data.data = self.mouse.data_on_device
                self.data_loaded_from_mouse.emit()
                logger.info("Loaded mouse data from cache: %s", cache_file_name)
                return

        class Worker(QRunnable):
            def run(inner_self): # type: ignore
                assert self.mouse is not None
                try:
                    self.mouse.data_on_device = self.mouse.connection.read_all(
                        lambda progress: logger.debug("Loading mouse data: %s", progress))
                    try:
                        with open(cache_file_name, 'wb') as f:
                            f.write(self.mouse.data_on_device)
                    except Exception as e:
                        logger.warning("Failed to save mouse data to cache: %s", e)
                    self.mouse.data.data = self.mouse.data_on_device
                    self.data_loaded_from_mouse.emit()
                except Exception as e:
                    logger.error("Failed to load mouse data: %s", e)
        QThreadPool.globalInstance().start(Worker())


def start_app() -> int:
    '''Creates the main window and starts the application event loop.'''
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()
