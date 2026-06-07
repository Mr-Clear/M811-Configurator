from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QWidget

from ui.button_widget import ButtonWidget
from ui.mouse_config import get_mouse_config
from ui.mouse_data import MouseData
from ui.vertical_tab_wiget import HorizontalTabBar, VerticalTabWidget


class ButtonsWidget(QWidget):
    '''Widget to show and modify mouse button data.'''
    selected_button_changed = Signal(int)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._data: MouseData | None = None
        self._selected_profile_index: int = 0
        self._selected_button_index: int = 0
        self._current_button_names: list[str] | None = None

        self.tab_widget = VerticalTabWidget()
        layout = QHBoxLayout(self)
        layout.addWidget(self.tab_widget)
        self.tab_widget.currentChanged.connect(self.selected_button_changed)

    def set_data(self, data: MouseData) -> None:
        '''Set the mouse data to display.'''
        self._data = data
        buttons_names = get_mouse_config(data.mouse_type).buttons
        if self._current_button_names != buttons_names:
            self._current_button_names = buttons_names
            self._update_button_names()
        else:
            self._update_buttons()

    def set_selected_profile_index(self, index: int) -> None:
        '''Set the currently selected profile index.'''
        self._selected_profile_index = index
        self._update_buttons()

    def set_selected_button_index(self, index: int) -> None:
        '''Set the currently selected button index.'''
        if self._selected_button_index != index:
            self._selected_button_index = index
        self.selected_button_changed.emit(index)

    def set_hovered_button_index(self, index: int) -> None:
        '''Set the currently hovered button index.'''
        tab_bar = self.tab_widget.tabBar()
        assert isinstance(tab_bar, HorizontalTabBar)
        tab_bar.set_hovered_tab(index)

    def _update_button_names(self) -> None:
        '''Update the tabs to show the buttons of the current profile.'''
        self.tab_widget.clear()
        if not self._current_button_names:
            return
        if self._data is None:
            return
        profile_data = self._data.get_profile_data(
            self._selected_profile_index)
        buttons = list(profile_data.buttons())
        if len(buttons) != len(self._current_button_names):
            raise ValueError(f"Profile has {len(buttons)} buttons, "
                             f"but expected {len(self._current_button_names)}")
        for button_index, button in enumerate(profile_data.buttons()):
            button_name = self._current_button_names[button_index]
            button_widget = ButtonWidget(button)
            self.tab_widget.addTab(button_widget, button_name)

        self.tab_widget.setCurrentIndex(self._selected_button_index)
        new_button_index = self.tab_widget.currentIndex()
        if new_button_index != self._selected_button_index:
            self.set_selected_button_index(new_button_index)

    def _update_buttons(self) -> None:
        '''Update the button widgets to show the current button data.'''
        if self._data is None:
            return
        profile_data = self._data.get_profile_data(
            self._selected_profile_index)
        for button_index, button in enumerate(profile_data.buttons()):
            button_widget = self.tab_widget.widget(button_index)
            if isinstance(button_widget, ButtonWidget):
                button_widget.set_data(button)
