from typing import TYPE_CHECKING

from ui.mouse_data.observable_value import Observable, Value

if TYPE_CHECKING:
    from . import MouseData

class Macro(Observable):
    """A single macro."""
    STEP_COUNT = 65
    def __init__(self, mouse: MouseData, steps: list[MacroStep]):
        if len(steps) != self.STEP_COUNT:
            raise ValueError(f"Macro must have {self.STEP_COUNT} steps, got {len(steps)}")
        super().__init__(mouse)
        self._steps = steps
        for step in self._steps:
            step.changed.connect(self.changed.emit)

    def step_count(self) -> int:
        for i, step in enumerate(self._steps):
            if not step.is_active():
                return i
        return len(self._steps)

    def to_json(self) -> list[object]:
        steps: list[object] = []
        for step in self._steps:
            if step.is_active():
                steps.append(step.to_json())
            else:
                break
        return steps


class MacroStep(Value):
    """Represents a single step of a macro."""
    def __init__(self, mouse: MouseData, offset: int):
        super().__init__(mouse, offset, 3)

    def is_active(self) -> bool:
        return self.raw_data[0] != 0x00

    def to_json(self) -> str:
        return f'0x{self.raw_data.hex()}'
