# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Callable
from typing import Any, Optional

import pygame_menu
from pygame_menu import locals

from tuxemon import formula, prepare
from tuxemon.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.monster import Monster
from tuxemon.platform.const import buttons
from tuxemon.platform.events import PlayerInput

MenuGameObj = Callable[[], object]


def fix_measure(measure: int, percentage: float) -> int:
    """it returns the correct measure based on percentage"""
    return round(measure * percentage)


class PartyState(PygameMenuState):
    """
    This state is responsible for the party menu.

    By clicking left, it gives access to the Character Menu.

    Shows details of the party (e.g. monster travelling distance,
    average level, etc.).

    """

    def __init__(self, **kwargs: Any) -> None:
        monsters: list[Monster] = []
        for element in kwargs.values():
            monsters = element["party"]
        if not monsters:
            raise ValueError("No monsters in the party")
        width, height = prepare.SCREEN_SIZE

        theme = self._setup_theme(prepare.BG_PARTY)
        theme.scrollarea_position = locals.POSITION_EAST
        theme.widget_alignment = locals.ALIGN_CENTER

        super().__init__(height=height, width=width)
        self.initialize_items(self.menu, monsters)
        self.reset_theme()

    def initialize_items(
        self,
        menu: pygame_menu.Menu,
        monsters: list[Monster],
    ) -> None:
        width = menu._width
        height = menu._height
        self.char = monsters[0].owner
        if self.char is None:
            raise ValueError(f"{monsters[0].name}'s owner not found")
        game_variables = self.char.game_variables
        menu._auto_centering = False
        # party
        lab1: Any = menu.add.label(
            title=T.translate("menu_party"),
            font_size=self.font_size_big,
            align=locals.ALIGN_LEFT,
            underline=True,
            float=True,
        )
        lab1.translate(fix_measure(width, 0.05), fix_measure(height, 0.15))
        # highest
        highest_level = game_variables.get("party_level_highest", 0)
        highest = T.translate("menu_party_level_highest")
        lab2: Any = menu.add.label(
            title=f"{highest}: {highest_level}",
            font_size=self.font_size_smaller,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        lab2.translate(fix_measure(width, 0.05), fix_measure(height, 0.25))
        # average
        average_level = game_variables.get("party_level_average", 0)
        average = T.translate("menu_party_level_average")
        lab3: Any = menu.add.label(
            title=f"{average}: {average_level}",
            font_size=self.font_size_smaller,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        lab3.translate(fix_measure(width, 0.05), fix_measure(height, 0.30))
        # lowest
        lowest_level = game_variables.get("party_level_lowest", 0)
        lowest = T.translate("menu_party_level_lowest")
        lab4: Any = menu.add.label(
            title=f"{lowest}: {lowest_level}",
            font_size=self.font_size_smaller,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        lab4.translate(fix_measure(width, 0.05), fix_measure(height, 0.35))

        total = sum(monster.steps for monster in monsters)
        # bond
        if self.char.find_item("friendship_scroll"):
            lab5: Any = menu.add.label(
                title=T.translate("menu_bond"),
                font_size=self.font_size_big,
                align=locals.ALIGN_LEFT,
                underline=True,
                float=True,
            )
            lab5.translate(fix_measure(width, 0.05), fix_measure(height, 0.45))
            if total > 0:
                _sorted = sorted(monsters, key=lambda x: x.steps, reverse=True)
                _bond = 0.50
                for monster in _sorted:
                    _bond += 0.05
                    _label = monster.name.upper()
                    bar: Any = menu.add.progress_bar(
                        f"{_label:<10}",
                        default=monster.bond,
                        font_size=self.font_size_smaller,
                        align=locals.ALIGN_LEFT,
                        progress_text_enabled=False,
                        float=True,
                    )
                    bar.translate(
                        fix_measure(width, 0.05), fix_measure(height, _bond)
                    )
        # steps
        if total > 0:
            _sorted = sorted(monsters, key=lambda x: x.steps, reverse=True)
            for monster in _sorted:
                steps = monster.steps
                unit = game_variables.get("unit_measure", prepare.METRIC)
                if unit == prepare.METRIC:
                    walked = formula.convert_km(steps)
                    unit_walked = prepare.U_KM
                else:
                    walked = formula.convert_mi(steps)
                    unit_walked = prepare.U_MI
                # labels
                params = {
                    "name": monster.name.upper(),
                    "walked": walked,
                    "unit": unit_walked,
                }
                lab6: Any = menu.add.label(
                    title=T.format("menu_party_traveled", params),
                    font_size=self.font_size_smaller,
                    align=locals.ALIGN_LEFT,
                )
                lab6.translate(
                    fix_measure(width, 0.35), fix_measure(height, 0.25)
                )

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        params = {"character": self.char}
        if event.button == buttons.LEFT and event.pressed:
            self.client.replace_state("CharacterState", kwargs=params)
        if (
            event.button in (buttons.BACK, buttons.B, buttons.A)
            and event.pressed
        ):
            self.client.pop_state()
        return None
