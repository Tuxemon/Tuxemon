from tuxemon import prepare
import pygame_menu
from tuxemon.tools import transform_resource_filename
from typing import Optional
from tuxemon.audio import get_sound_filename

_theme: Optional[pygame_menu.themes.Theme] = None


def get_theme() -> pygame_menu.themes.Theme:
    """Get Tuxemon default theme."""
    global _theme

    if _theme is not None:
        return _theme

    font_filename = prepare.fetch("font", "PressStart2P.ttf")
    tuxemon_border = pygame_menu.baseimage.BaseImage(
        image_path=transform_resource_filename("gfx/dialog-borders01.png"),
    ).scale(5, 5)

    tuxemon_background_center_rect = tuxemon_border.get_rect()
    tuxemon_background_center_rect = tuxemon_background_center_rect.inflate(
        - 2 * tuxemon_background_center_rect.width // 3,
        - 2 * tuxemon_background_center_rect.height // 3,
    )

    tuxemon_background = tuxemon_border.copy().crop_rect(tuxemon_background_center_rect)

    theme = pygame_menu.Theme(
        background_color=tuxemon_background,
        title_font=font_filename,
        widget_font=font_filename,
        widget_alignment=pygame_menu.locals.ALIGN_LEFT,
        title_font_size=20,
        widget_font_size=26,
        title=False,
        widget_selection_effect=pygame_menu.widgets.LeftArrowSelection(),
        widget_font_color=(0, 0, 0),
        selection_color=(0, 0, 0),
        border_color=tuxemon_border,
        scrollarea_position=pygame_menu.locals.SCROLLAREA_POSITION_NONE,
        widget_padding=(10, 20),
    )

    _theme = theme
    return _theme


_sound_engine: Optional[pygame_menu.sound.Sound] = None


def get_sound_engine() -> pygame_menu.sound.Sound:
    """Get Tuxemon default sound engine."""
    global _sound_engine

    if _sound_engine is not None:
        return _sound_engine

    sound_engine = pygame_menu.sound.Sound()
    sound_engine.set_sound(
        pygame_menu.sound.SOUND_TYPE_WIDGET_SELECTION,
        get_sound_filename("sound_menu_select"),
    )

    _sound_engine = sound_engine
    return _sound_engine
