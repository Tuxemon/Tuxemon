# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from collections.abc import Callable
from functools import partial

import pygame_menu
from pygame_menu import locals
from pygame_menu.widgets.selection.highlight import HighlightSelection

from tuxemon import prepare
from tuxemon.db import MonsterModel, db
from tuxemon.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.session import local_session
from tuxemon.tools import open_dialog

MenuGameObj = Callable[[], object]
lookup_cache: dict[str, MonsterModel] = {}


def fix_measure(measure: int, percentage: float) -> int:
    """it returns the correct measure based on percentage"""
    return round(measure * percentage)


def _lookup_monsters() -> None:
    monsters = list(db.database["monster"])
    for mon in monsters:
        results = db.lookup(mon, table="monster")
        if results.txmn_id > 0:
            lookup_cache[mon] = results


class MinigameState(PygameMenuState):
    """Menu for the Journal Info state.

    Shows details of the single monster."""

    def add_menu_items(
        self,
        menu: pygame_menu.Menu,
    ) -> None:
        width, height = prepare.SCREEN_SIZE
        # name
        name = T.translate("who_is_that")
        menu.add.label(
            title=f"{name}",
            label_id="question",
            font_size=self.font_size_big,
            align=locals.ALIGN_CENTER,
            underline=True,
        )
        # image
        data = list(lookup_cache.values())
        tuxemon: MonsterModel
        tuxemon = random.choice(data)
        self.tuxemon = tuxemon
        new_image = self._create_image(
            f"gfx/sprites/battle/{tuxemon.slug}-front.png"
        )
        new_image.scale(prepare.SCALE, prepare.SCALE)
        menu.add.image(image_path=new_image.copy())
        choice = random.sample(data, 5)
        pos = random.choice(range(len(choice)))
        if tuxemon not in choice:
            choice.pop()
            choice.insert(pos, tuxemon)

        def checking(mon: MonsterModel) -> None:
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
                font_size=self.font_size_small,
                button_id=txmn.slug,
                selection_effect=HighlightSelection(),
            )
            for txmn in choice
        ]
        for choice in labels:
            f.pack(choice, align=locals.ALIGN_CENTER)

    def __init__(self) -> None:
        if not lookup_cache:
            _lookup_monsters()
        width, height = prepare.SCREEN_SIZE

        theme = self._setup_theme(prepare.BG_MINIGAME)
        theme.scrollarea_position = locals.POSITION_EAST
        theme.widget_alignment = locals.ALIGN_CENTER

        super().__init__(height=height, width=width)

        self.add_menu_items(self.menu)
        self.reset_theme()
