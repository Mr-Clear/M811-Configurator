from typing import TYPE_CHECKING

from ui.mouse_data.button import Button
from ui.mouse_data.color import Color
from ui.mouse_data.dpis import Dpis
from ui.mouse_data.lighting import Lighting
from ui.mouse_data.observable_value import Observable
from ui.mouse_data.poll_rate import PollRate
from ui.mouse_data.scroll_speed import ScrollSpeed

if TYPE_CHECKING:
    from . import MouseData

class Mode(Observable):
    def __init__(self, mouse: MouseData, scroll_speed: ScrollSpeed, poll_rate: PollRate, dpis: Dpis, effects: Lighting, buttons: list[Button], color: Color):
        super().__init__(mouse)
        self._scroll_speed = scroll_speed
        self._scroll_speed.changed.connect(self.changed.emit)
        self._poll_rate = poll_rate
        self._poll_rate.changed.connect(self.changed.emit)
        self._dpis = dpis
        self._dpis.changed.connect(self.changed.emit)
        self._effects = effects
        self._effects.changed.connect(self.changed.emit)
        self._buttons = buttons
        for button in self._buttons:
            button.changed.connect(self.changed.emit)
        self._color = color
        self._color.changed.connect(self.changed.emit)

    def to_json(self) -> dict[str, object]:
        return {
            "scroll_speed": self._scroll_speed.to_json(),
            "poll_rate": self._poll_rate.to_json(),
            "dpis": self._dpis.to_json(),
            "effect": self._effects.to_json(),
            "buttons": [button.to_json() for button in self._buttons],
            "color": self._color.to_json(),
        }
