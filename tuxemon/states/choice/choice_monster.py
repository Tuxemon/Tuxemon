# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from typing import Any

from pygame_menu.locals import ALIGN_CENTER, POSITION_EAST
from pygame_menu.widgets.selection.highlight import HighlightSelection

from tuxemon import prepare
from tuxemon.animation import Animation
from tuxemon.db import db
from tuxemon.menu.menu import PygameMenuState
from tuxemon.menu.theme import get_theme

ChoiceMenuGameObj = Callable[[], None]
MAX_MENU_ELEMENTS = 15
MAX_MENU_HEIGHT_PERCENTAGE = 0.8
ANIMATION_DURATION = 0.2
ANIMATION_SIZE = 1.0
MENU_WIDGETS = 3
MENU_COLUMNS = 5
SCALE_SPRITE = 0.4
VERTICAL_FILL = 15


class ChoiceMonster(PygameMenuState):
    """
    Game state with a graphic box and monsters (images) + labels.

    """

    def __init__(
        self,
        menu: Sequence[tuple[str, str, Callable[[], None]]] = (),
        escape_key_exits: bool = False,
        **kwargs: Any,
    ) -> None:
        theme = get_theme()
        if len(menu) > MAX_MENU_ELEMENTS:
            theme.scrollarea_position = POSITION_EAST

        rows = math.ceil(len(menu) / MENU_COLUMNS) * MENU_WIDGETS
        super().__init__(columns=MENU_COLUMNS, rows=rows, **kwargs)

        for name, slug, callback in menu:
            self.add_monster_menu_item(name, slug, callback)

        self.animation_size = 0.0
        self.escape_key_exits = escape_key_exits

    def add_monster_menu_item(
        self,
        name: str,
        slug: str,
        callback: Callable[[], None],
    ) -> None:
        try:
            monster = db.lookup(slug, table="monster")
        except KeyError:
            raise RuntimeError(f"Monster {slug} not found")

        path = f"gfx/sprites/battle/{monster.slug}-front.png"
        new_image = self._create_image(path)
        new_image.scale(
            prepare.SCALE * SCALE_SPRITE, prepare.SCALE * SCALE_SPRITE
        )

        def open_journal() -> None:
            action = self.client.event_engine
            _set_tuxepedia = ["player", monster.slug, "caught"]
            action.execute_action("set_tuxepedia", _set_tuxepedia, True)
            param = {"monster": monster}
            self.client.push_state("JournalInfoState", kwargs=param)
            action.execute_action("clear_tuxepedia", [monster.slug], True)

        self.menu.add.banner(
            new_image,
            open_journal,
            align=ALIGN_CENTER,
            selection_effect=HighlightSelection(),
        )
        self.menu.add.button(
            name,
            callback,
            font_size=self.font_size_small,
            align=ALIGN_CENTER,
            selection_effect=HighlightSelection(),
        )
        self.menu.add.vertical_fill(VERTICAL_FILL)

    def update_animation_size(self) -> None:
        width, height = prepare.SCREEN_SIZE
        widgets_size = self.menu.get_size(widget=True)

        _width = widgets_size[0]
        _height = widgets_size[1]

        if _width >= width:
            _width = width
        if _height >= height:
            _height = int(height * MAX_MENU_HEIGHT_PERCENTAGE)

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

        ani = self.animate(
            self, animation_size=ANIMATION_SIZE, duration=ANIMATION_DURATION
        )
        ani.update_callback = self.update_animation_size

        return ani
