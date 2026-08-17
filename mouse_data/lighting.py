from enum import Enum
from typing import TYPE_CHECKING

from mouse_data.color import Color
from mouse_data.observable_value import IntValue, Observable

if TYPE_CHECKING:
    from . import MouseData


class Lighting(Observable):
    """Lighting of a mode."""

    def __init__(self, mouse: MouseData, offset: int):
        super().__init__(mouse)
        self._color = Color(mouse, offset)
        self._color.changed.connect(self.changed.emit)
        self._speed = IntValue(mouse, offset + 4, 1, 0, 5)
        self._speed.changed.connect(self.changed.emit)
        self._brightness = IntValue(mouse, offset + 6, 1, 0, 3)
        self._brightness.changed.connect(self.changed.emit)
        self._config = LightingEffect(mouse, offset + 3)

    @property
    def color(self) -> Color:
        return self._color

    @property
    def config(self) -> LightingEffect:
        return self._config

    @property
    def speed(self) -> IntValue:
        return self._speed

    @property
    def brightness(self) -> IntValue:
        return self._brightness

    def to_json(self) -> dict[str, object]:
        return {
            "mode": self.config.to_json(),
            "color": self.color.to_json(),
            "brightness": self.brightness.to_json(),
            "speed": self.speed.to_json()
        }


class LightingEffect(Observable):
    """The lighting effect of a mode."""
    def __init__(self, mouse: MouseData, offset: int):
        super().__init__(mouse)
        self._low_byte = IntValue(mouse, offset, 1, 0, 255)
        self._high_byte = IntValue(mouse, offset + 2, 1, 0, 255)
        self._low_byte.changed.connect(self.changed.emit)
        self._high_byte.changed.connect(self.changed.emit)

    def to_json(self) -> str:
        return f'0x{self._low_byte.value:02x}{self._high_byte.value:02x}'


class LightingEffectType(Enum):
    """Represents the effect of a mode."""
    STATIC = (0, 0)
    BREATHING = (1, 0)
    WAVE = (2, 0)
    REACTIVE = (3, 0)
    RIPPLE = (4, 0)
    CYCLE = (5, 0)

    @property
    def name(self) -> str:
        return self._name_.replace("_", " ").title()
