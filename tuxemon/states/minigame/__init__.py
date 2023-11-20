# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from collections.abc import Callable
from functools import partial

import pygame_menu
from pygame_menu import locals
from pygame_menu.locals import POSITION_CENTER
from pygame_menu.widgets.selection.highlight import HighlightSelection

from tuxemon import prepare, tools
from tuxemon.db import MonsterModel, db
from tuxemon.locale import T
from tuxemon.menu.menu import BACKGROUND_COLOR, PygameMenuState
from tuxemon.menu.theme import get_theme
from tuxemon.monster import Monster
from tuxemon.session import local_session
from tuxemon.tools import open_dialog

MenuGameObj = Callable[[], object]


def fix_measure(measure: int, percentage: float) -> int:
    """it returns the correct measure based on percentage"""
    return round(measure * percentage)


class MinigameState(PygameMenuState):
    """Menu for the Journal Info state.

    Shows details of the single monster."""

    def add_menu_items(
        self,
        menu: pygame_menu.Menu,
    ) -> None:
        # data
        monsters = list(db.database["monster"])
        data = []
        for mon in monsters:
            results = db.lookup(mon, table="monster")
            if results.txmn_id > 0:
                data.append(results)

        # name
        name = T.translate("who_is_that")
        menu.add.label(
            title=f"{name}",
            label_id="question",
            font_size=30,
            align=locals.ALIGN_CENTER,
            underline=True,
        )
        # image
        tuxemon: MonsterModel
        tuxemon = random.choice(data)
        self.tuxemon = tuxemon
        new_image = pygame_menu.BaseImage(
            tools.transform_resource_filename(
                "gfx/sprites/battle/" + tuxemon.slug + "-front.png"
            ),
        )
        new_image.scale(prepare.SCALE, prepare.SCALE)
        menu.add.image(image_path=new_image.copy())
        choice = random.sample(data, 5)
        pos = random.choice(range(len(choice)))
        if tuxemon not in choice:
            choice.pop()
            choice.insert(pos, tuxemon)

        def checking(mon: Monster) -> None:
            if mon.slug == self.tuxemon.slug:
                self.client.replace_state("MinigameState")
            else:
                open_dialog(local_session, [T.translate("generic_wrong")])

        # replies
        width = menu._width
        f = menu.add.frame_h(
            width=fix_measure(width, 0.95),
            height=fix_measure(width, 0.05),
            frame_id="evolutions",
            align=locals.ALIGN_CENTER,
        )
        f._relax = True
        labels = [
            menu.add.button(
                T.translate(txmn.slug),
                partial(checking, txmn),
                font_size=20,
                button_id=txmn.slug,
                selection_effect=HighlightSelection(),
            )
            for txmn in choice
        ]
        for choice in labels:
            f.pack(choice, align=locals.ALIGN_CENTER)

    def __init__(self) -> None:
        width, height = prepare.SCREEN_SIZE

        background = pygame_menu.BaseImage(
            image_path=tools.transform_resource_filename(
                "gfx/ui/item/bg_pcstate.png"
            ),
            drawing_position=POSITION_CENTER,
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
        theme.background_color = BACKGROUND_COLOR
        theme.widget_alignment = locals.ALIGN_LEFT
