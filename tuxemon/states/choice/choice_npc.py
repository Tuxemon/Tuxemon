# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from typing import Any

import pygame_menu
from pygame_menu.locals import ALIGN_CENTER, POSITION_CENTER, POSITION_EAST
from pygame_menu.widgets.selection.highlight import HighlightSelection

from tuxemon import prepare
from tuxemon.animation import Animation
from tuxemon.db import db
from tuxemon.menu.menu import PygameMenuState
from tuxemon.menu.theme import get_theme
from tuxemon.tools import transform_resource_filename

ChoiceMenuGameObj = Callable[[], None]


def fix_measure(measure: int, percentage: float) -> int:
    """it returns the correct measure based on percentage"""
    return round(measure * percentage)


class ChoiceNpc(PygameMenuState):
    """
    Game state with a graphic box and NPCs (images) + labels.

    """

    def __init__(
        self,
        menu: Sequence[tuple[str, str, Callable[[], None]]] = (),
        escape_key_exits: bool = False,
        **kwargs: Any,
    ) -> None:
        theme = get_theme()
        if len(menu) > 12:
            theme.scrollarea_position = POSITION_EAST

        columns = 4
        num_widgets = 3
        rows = math.ceil(len(menu) / columns) * num_widgets

        super().__init__(columns=columns, rows=rows, **kwargs)

        for name, slug, callback in menu:
            try:
                npc = db.lookup(slug, table="npc")
            except KeyError:
                raise RuntimeError(f"NPC {slug} not found")
            path = f"gfx/sprites/player/{npc.template.combat_front}.png"
            new_image = pygame_menu.BaseImage(
                transform_resource_filename(path),
                drawing_position=POSITION_CENTER,
            )
            new_image.scale(prepare.SCALE * 0.4, prepare.SCALE * 0.4)
            self.menu.add.image(
                new_image,
                align=ALIGN_CENTER,
            )
            # replace slug not translated
            if name == slug:
                name = "???"
            self.menu.add.button(
                name,
                callback,
                font_size=self.font_size_smaller,
                align=ALIGN_CENTER,
                selection_effect=HighlightSelection(),
            )
            self.menu.add.vertical_fill(10)

        self.animation_size = 0.0
        self.escape_key_exits = escape_key_exits

    def update_animation_size(self) -> None:
        width, height = prepare.SCREEN_SIZE
        widgets_size = self.menu.get_size(widget=True)

        _width = widgets_size[0]
        _height = widgets_size[1]

        # block width if more than screen width
        if _width >= width:
            _width = width
        if _height >= height:
            _height = int(height * 0.8)

        self.menu.resize(
            max(1, int(_width * self.animation_size)),
            max(1, int(_height * self.animation_size)),
        )

    def animate_open(self) -> Animation:
        """
        Animate the menu popping in.

        Returns:
            Popping in animation.

        """
        self.animation_size = 0.0

        ani = self.animate(self, animation_size=1.0, duration=0.2)
        ani.update_callback = self.update_animation_size

        return ani
