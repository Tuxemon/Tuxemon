# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from typing import Callable

import pygame_menu
from pygame_menu import baseimage, locals

from tuxemon import formula, graphics, prepare
from tuxemon.db import SeenStatus, db
from tuxemon.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.menu.theme import get_theme
from tuxemon.session import local_session

MenuGameObj = Callable[[], object]


def fix_width(screen_x: int, pos_x: float) -> int:
    """it returns the correct width based on percentage"""
    value = round(screen_x * pos_x)
    return value


def fix_height(screen_y: int, pos_y: float) -> int:
    """it returns the correct height based on percentage"""
    value = round(screen_y * pos_y)
    return value


class PlayerState(PygameMenuState):
    """Menu for the Journal Info state.

    Shows details of the single monster."""

    def add_menu_items(
        self,
        menu: pygame_menu.Menu,
    ) -> None:

        width = menu._width
        height = menu._height

        player = local_session.player

        if player.name == "":
            name = T.translate(player.slug).upper()
        else:
            name = player.name.upper()

        # tuxepedia data
        monsters = list(db.database["monster"])
        filters = []
        for mon in monsters:
            results = db.lookup(mon, table="monster")
            if results.txmn_id > 0:
                filters.append(results)
        tuxepedia = list(player.tuxepedia.values())
        caught = tuxepedia.count(SeenStatus.caught)
        seen = tuxepedia.count(SeenStatus.seen) + caught
        percentage = formula.sync(player, seen, len(filters))

        msg_progress = T.format(
            "tuxepedia_progress", {"value": str(percentage)}
        )
        msg_seen = T.format(
            "tuxepedia_data_seen",
            {"param": str(seen), "all": str(len(filters))},
        )
        msg_caught = T.format(
            "tuxepedia_data_caught",
            {"param": str(caught), "all": str(len(filters))},
        )
        date_begin = formula.today_ordinal() - int(
            player.game_variables["date_start_game"]
        )
        msg_begin = T.format(
            "player_start_adventure",
            {"date": str(date_begin)},
        )

        # name
        menu._auto_centering = False
        menu.add.label(
            title=name,
            label_id="name",
            font_size=30,
            align=locals.ALIGN_LEFT,
            underline=True,
            float=True,
        ).translate(fix_width(width, 0.45), fix_height(height, 0.15))
        # money
        money = player.money["player"]
        menu.add.label(
            title=T.translate("wallet") + ": " + str(money),
            label_id="money",
            font_size=15,
            align=locals.ALIGN_LEFT,
            float=True,
        ).translate(fix_width(width, 0.45), fix_height(height, 0.25))
        # seen
        menu.add.label(
            title=msg_seen,
            label_id="seen",
            font_size=15,
            align=locals.ALIGN_LEFT,
            float=True,
        ).translate(fix_width(width, 0.45), fix_height(height, 0.30))
        # caught
        menu.add.label(
            title=msg_caught,
            label_id="caught",
            font_size=15,
            align=locals.ALIGN_LEFT,
            float=True,
        ).translate(fix_width(width, 0.45), fix_height(height, 0.35))
        # begin adventure
        menu.add.label(
            title=msg_begin,
            label_id="begin",
            font_size=15,
            align=locals.ALIGN_LEFT,
            float=True,
        ).translate(fix_width(width, 0.45), fix_height(height, 0.40))
        # % tuxepedia
        menu.add.label(
            title=msg_progress,
            label_id="progress",
            font_size=15,
            align=locals.ALIGN_LEFT,
            float=True,
        ).translate(fix_width(width, 0.45), fix_height(height, 0.10))
        # image
        new_image = pygame_menu.BaseImage(
            graphics.transform_resource_filename(
                "gfx/sprites/player/" + player.combat_front
            ),
        )
        new_image.scale(prepare.SCALE, prepare.SCALE)
        image_widget = menu.add.image(image_path=new_image.copy())
        image_widget.set_float(origin_position=True)
        image_widget.translate(
            fix_width(width, 0.17), fix_height(height, 0.08)
        )

    def __init__(self, **kwargs) -> None:

        width, height = prepare.SCREEN_SIZE

        background = pygame_menu.BaseImage(
            image_path=graphics.transform_resource_filename(
                "gfx/ui/item/player_info.png"
            ),
            drawing_position=baseimage.POSITION_CENTER,
        )
        theme = get_theme()
        theme.scrollarea_position = locals.POSITION_EAST
        theme.background_color = background
        theme.widget_alignment = locals.ALIGN_CENTER

        super().__init__(height=height, width=width)

        self.add_menu_items(self.menu)
        self.repristinate()

    def repristinate(self) -> None:
        """Repristinate original theme (color, alignment, etc.)"""
        theme = get_theme()
        theme.scrollarea_position = locals.SCROLLAREA_POSITION_NONE
        theme.background_color = PygameMenuState.background_color
        theme.widget_alignment = locals.ALIGN_LEFT
