# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from typing import Optional

import pygame
import pygame_menu
from pygame_menu.widgets.core.selection import Selection
from pygame_menu.widgets.core.widget import Widget

from tuxemon import prepare
from tuxemon.audio import get_sound_filename
from tuxemon.tools import transform_resource_filename

_theme: Optional[pygame_menu.themes.Theme] = None


class TuxemonArrowSelection(Selection):
    def __init__(self) -> None:
        # Call the constructor of the Selection providing the left, right,
        # top and bottom margins of your Selection effect box.
        #
        #  --------------------------
        # |          ^ top           |  In this example, XXXX represents the
        # | left  XXXXXXXXXXXX right |  Widget to be Selected.
        # |<----> XXXXXXXXXXXX<----->|  left, right, top and bottom must be described
        # |         v bottom         |  in pixels
        #  --------------------------
        #

        arrow = pygame_menu.baseimage.BaseImage(
            image_path=transform_resource_filename("gfx/arrow.png"),
        ).scale(5, 5, smooth=False)

        super().__init__(
            margin_left=arrow.get_width(),
            margin_right=0,
            margin_top=0,
            margin_bottom=0,
        )
        self.arrow = arrow

    def draw(
        self,
        surface: pygame.surface.Surface,
        widget: Widget,
    ) -> Selection:
        """
        This method receives the surface to draw the selection and the
        widget itself. For retrieving the Selection coordinates the rect
        object from widget should be used.
        """
        widget_rect = widget.get_rect()
        position = (
            widget_rect.topleft[0] - self.arrow.get_width(),
            widget_rect.topleft[1],
        )

        self.arrow.draw(
            surface,
            area=self.arrow.get_rect(),
            position=position,
        )
        return self


def get_theme() -> pygame_menu.themes.Theme:
    """Get Tuxemon default theme."""
    global _theme

    if _theme is not None:
        return _theme

    if prepare.CONFIG.locale == "zh_CN":
        font_filename = prepare.fetch("font", prepare.FONT_CHINESE)
    elif prepare.CONFIG.locale == "ja":
        font_filename = prepare.fetch("font", prepare.FONT_JAPANESE)
    else:
        font_filename = prepare.fetch("font", prepare.FONT_BASIC)
    tuxemon_border = pygame_menu.baseimage.BaseImage(
        image_path=transform_resource_filename("gfx/dialog-borders01.png"),
    ).scale(5, 5, smooth=False)

    tuxemon_background_center_rect = tuxemon_border.get_rect()
    tuxemon_background_center_rect = tuxemon_background_center_rect.inflate(
        -2 * tuxemon_background_center_rect.width // 3,
        -2 * tuxemon_background_center_rect.height // 3,
    )

    tuxemon_background = tuxemon_border.copy().crop_rect(
        tuxemon_background_center_rect
    )

    theme = pygame_menu.Theme(
        background_color=tuxemon_background,
        title_font=font_filename,
        widget_font=font_filename,
        widget_alignment=pygame_menu.locals.ALIGN_LEFT,
        title_font_size=20,
        widget_font_size=26,
        title=False,
        widget_selection_effect=TuxemonArrowSelection(),
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
