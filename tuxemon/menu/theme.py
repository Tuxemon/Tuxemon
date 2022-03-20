from tuxemon import prepare
import pygame_menu
from tuxemon.tools import transform_resource_filename
from typing import Final


FONT_FILENAME: Final = prepare.fetch("font", "PressStart2P.ttf")

TUXEMON_BORDER: Final = pygame_menu.baseimage.BaseImage(
    image_path=transform_resource_filename("gfx/dialog-borders01.png"),
).scale(5, 5)

_tuxemon_background_center_rect = TUXEMON_BORDER.get_rect()
_tuxemon_background_center_rect = _tuxemon_background_center_rect.inflate(
    - 2 * _tuxemon_background_center_rect.width // 3,
    - 2 * _tuxemon_background_center_rect.height // 3,
)

TUXEMON_BACKGROUND: Final = TUXEMON_BORDER.copy().crop_rect(_tuxemon_background_center_rect)

TUXEMON_THEME: Final = pygame_menu.Theme(
    background_color=TUXEMON_BACKGROUND,
    title_font=FONT_FILENAME,
    widget_font=FONT_FILENAME,
    title_font_size=20,
    widget_font_size=26,
    title=False,
    widget_selection_effect=pygame_menu.widgets.LeftArrowSelection(),
    widget_font_color=(0, 0, 0),
    selection_color=(0, 0, 0),
    border_color=TUXEMON_BORDER,
)