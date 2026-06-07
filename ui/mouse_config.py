'''Defines the MouseConfig dataclass and a mapping of MouseType to MouseConfig.'''
from dataclasses import dataclass

from mouse import MouseType

@dataclass
class MouseConfig:
    '''Configures how a mouse is displayed and supported in the UI.'''
    image: str
    buttons: list[str]
    fully_supported: bool = True


mouse_configs: dict[MouseType | None, MouseConfig] = {
    MouseType.M811: MouseConfig(
        image="res/M811.svg",
        buttons=['LMB', 'RMB', 'MMB', 'Back', 'Forward', 'DPI+',
                 'DPI-', 'Mode', '1', '2', '3', '4', '5', '6', '7', '8'],
    ),
    None: MouseConfig(
        image="res/UnknownRedragon.svg",
        buttons=[str(i) for i in range(1, 20)],
        fully_supported=False,
    ),
}

def get_mouse_config(mouse_type: MouseType | None) -> MouseConfig:
    '''Get the MouseConfig for a given MouseType, or a default config if the type is unknown.'''
    return mouse_configs.get(mouse_type, mouse_configs[None])
