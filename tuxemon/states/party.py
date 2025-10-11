# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Callable
from typing import Any, ClassVar, Optional

import pygame_menu
from pygame_menu import locals

from tuxemon import formula, prepare
from tuxemon.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.monster import Monster
from tuxemon.platform.const import buttons
from tuxemon.platform.events import PlayerInput
from tuxemon.tools import fix_measure

MenuGameObj = Callable[[], object]


class PartyState(PygameMenuState):
    """
    This state is responsible for the party menu.

    By clicking left, it gives access to the Character Menu.

    Shows details of the party (e.g. monster travelling distance,
    average level, etc.).
    """

    name: ClassVar[str] = "PartyState"

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
        fxw: Callable[[float], int] = lambda r: fix_measure(menu._width, r)
        fxh: Callable[[float], int] = lambda r: fix_measure(menu._height, r)
        self.char = monsters[0].get_owner()
        menu._auto_centering = False
        # party
        lab1: Any = menu.add.label(
            title=T.translate("menu_party"),
            font_size=self.font_type.big,
            align=locals.ALIGN_LEFT,
            underline=True,
            float=True,
        )
        lab1.translate(fxw(0.05), fxh(0.15))
        # levels
        level_lowest = self.char.party.level_lowest
        level_highest = self.char.party.level_highest
        level_average = self.char.party.level_average
        party_alignment = self.char.party.get_alignment()
        # highest
        highest = T.translate("menu_party_level_highest")
        lab2: Any = menu.add.label(
            title=f"{highest}: {level_highest or 0}",
            font_size=self.font_type.smaller,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        lab2.translate(fxw(0.05), fxh(0.25))
        # average
        average = T.translate("menu_party_level_average")
        lab3: Any = menu.add.label(
            title=f"{average}: {level_average or 0}",
            font_size=self.font_type.smaller,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        lab3.translate(fxw(0.05), fxh(0.30))
        # lowest
        lowest = T.translate("menu_party_level_lowest")
        lab4: Any = menu.add.label(
            title=f"{lowest}: {level_lowest or 0}",
            font_size=self.font_type.smaller,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        lab4.translate(fxw(0.05), fxh(0.35))
        # alignment
        if party_alignment:
            alignment = T.translate("menu_party_alignment")
            lab7: Any = menu.add.label(
                title=f"{alignment}: {T.translate(party_alignment)}",
                font_size=self.font_type.smaller,
                align=locals.ALIGN_LEFT,
                float=True,
            )
            lab7.translate(fxw(0.05), fxh(0.40))

        total = sum(monster.steps for monster in monsters)
        # bond
        if self.char.items.find_item("friendship_scroll"):
            lab5: Any = menu.add.label(
                title=T.translate("menu_bond"),
                font_size=self.font_type.big,
                align=locals.ALIGN_LEFT,
                underline=True,
                float=True,
            )
            lab5.translate(fxw(0.05), fxh(0.45))
            if total > 0:
                _sorted = sorted(monsters, key=lambda x: x.steps, reverse=True)
                _bond = 0.50
                for monster in _sorted:
                    _bond += 0.05
                    _label = monster.name.upper()
                    bar: Any = menu.add.progress_bar(
                        f"{_label:<10}",
                        default=monster.bond_handler.bond,
                        font_size=self.font_type.smaller,
                        align=locals.ALIGN_LEFT,
                        progress_text_enabled=False,
                        float=True,
                    )
                    bar.translate(fxw(0.05), fxh(_bond))
        # steps
        if total > 0:
            _sorted = sorted(monsters, key=lambda x: x.steps, reverse=True)
            for monster in _sorted:
                steps = monster.steps
                unit = self.client.config.unit_measure
                if unit == "metric":
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
                    font_size=self.font_type.smaller,
                    align=locals.ALIGN_LEFT,
                )
                lab6.translate(fxw(0.35), fxh(0.25))

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        params = {"character": self.char}
        if event.button == buttons.LEFT and event.pressed:
            self.client.replace_state("CharacterState", kwargs=params)
        if (
            event.button in (buttons.BACK, buttons.B, buttons.A)
            and event.pressed
        ):
            self.client.remove_state_by_name("PartyState")
        return None
