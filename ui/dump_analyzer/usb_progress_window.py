from PySide6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QProgressBar


def _format_size(size: int | float) -> str:
    for unit in ("", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"):
        if abs(size) < 1024.0:
            return f"{size:3.1f}{unit}B"
        size /= 1024.0
    return f"{size:.1f}YiB"


class USBProgressWindow(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("USB Transfer Progress")
        self.setFixedSize(300, 100)

        layout = QVBoxLayout(self)
        self.title_label = QLabel("Transferring data...", self)
        self.title_label.setStyleSheet("font-weight: bold; font-size: 18px; qproperty-alignment: AlignCenter;")
        self.progress_label = QLabel("0%", self)
        self.progress_label.setStyleSheet("font-weight: bold; font-size: 14px; qproperty-alignment: AlignCenter;")
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.title_label)
        layout.addWidget(self.progress_label)
        layout.addWidget(self.progress_bar)

    def show(self) -> None:
        super().show()
        QApplication.processEvents()  # Ensure the UI updates immediately

    def _update_progress(self) -> None:
        progress = self.progress_bar.value()
        target = self.progress_bar.maximum()
        self.progress_label.setText(f"{_format_size(progress)} / {_format_size(target)}")
        QApplication.processEvents()  # Ensure the UI updates during long operations

    def set_title(self, value: str) -> None:
        self.title_label.setText(value)

    def set_target_size(self, value: int) -> None:
        self.progress_bar.setMaximum(value)
        self.progress_label.setText(f"0 / {_format_size(value)}")
        self._update_progress()

    def set_progress(self, value: int) -> None:
        self.progress_bar.setValue(value)
        self._update_progress()
