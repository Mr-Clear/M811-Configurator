from typing import TYPE_CHECKING

from mouse_data.button import Button
from mouse_data.color import Color
from mouse_data.dpis import Dpis
from mouse_data.lighting import Lighting
from mouse_data.observable_value import Observable
from mouse_data.poll_rate import PollRate
from mouse_data.scroll_speed import ScrollSpeed

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

    @property
    def buttons(self) -> list[Button]:
        return self._buttons
    def button(self, index: int) -> Button:
        return self._buttons[index]

    @property
    def scroll_speed(self) -> ScrollSpeed:
        return self._scroll_speed

    @property
    def poll_rate(self) -> PollRate:
        return self._poll_rate

    @property
    def dpis(self) -> Dpis:
        return self._dpis

    @property
    def effects(self) -> Lighting:
        return self._effects

    @property
    def color(self) -> Color:
        return self._color

    def to_json(self) -> dict[str, object]:
        return {
            "scroll_speed": self._scroll_speed.to_json(),
            "poll_rate": self._poll_rate.to_json(),
            "dpis": self._dpis.to_json(),
            "effect": self._effects.to_json(),
            "buttons": [button.to_json() for button in self._buttons],
            "color": self._color.to_json(),
        }
