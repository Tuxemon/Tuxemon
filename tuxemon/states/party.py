# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from pygame_menu.locals import ALIGN_CENTER, ALIGN_LEFT, POSITION_EAST
from pygame_menu.menu import Menu

from tuxemon import formula
from tuxemon.entity.party import PartyHandler
from tuxemon.locale.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.monster.monster import Monster
from tuxemon.platform.const import buttons
from tuxemon.platform.const.graphics import BG_PARTY
from tuxemon.platform.const.sizes import U_KM, U_MI
from tuxemon.tools import fix_measure

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.platform.events import PlayerInput


class PartyState(PygameMenuState):
    """
    This state is responsible for the party menu.

    By clicking left, it gives access to the Character Menu.

    Shows details of the party (e.g. monster travelling distance,
    average level, etc.).
    """

    name: ClassVar[str] = "PartyState"

    def __init__(
        self, client: BaseClient, party: PartyHandler, **kwargs: Any
    ) -> None:
        self.party = party
        self.char = party.owner
        width, height = client.context.resolution
        super().__init__(client=client, height=height, width=width, **kwargs)

        theme = self._setup_theme(BG_PARTY)
        theme.scrollarea_position = POSITION_EAST
        theme.widget_alignment = ALIGN_CENTER
        self._menu_config["theme"] = theme

        self.initialize_items(self.menu, self.party.monsters)
        self.reset_theme()

    def initialize_items(
        self,
        menu: Menu,
        monsters: list[Monster],
    ) -> None:
        def fxw(r: float) -> int:
            return fix_measure(menu._width, r)

        def fxh(r: float) -> int:
            return fix_measure(menu._height, r)

        menu._auto_centering = False
        # party
        lab1: Any = menu.add.label(
            title=T.translate("menu_party"),
            font_size=self.font_type.big,
            align=ALIGN_LEFT,
            underline=True,
            float=True,
        )
        lab1.translate(fxw(0.05), fxh(0.15))
        # levels
        level_lowest = self.party.level_lowest
        level_highest = self.party.level_highest
        level_average = self.party.level_average
        party_alignment = self.party.alignment
        # highest
        highest = T.translate("menu_party_level_highest")
        lab2: Any = menu.add.label(
            title=f"{highest}: {level_highest or 0}",
            font_size=self.font_type.smaller,
            align=ALIGN_LEFT,
            float=True,
        )
        lab2.translate(fxw(0.05), fxh(0.25))
        # average
        average = T.translate("menu_party_level_average")
        lab3: Any = menu.add.label(
            title=f"{average}: {level_average or 0}",
            font_size=self.font_type.smaller,
            align=ALIGN_LEFT,
            float=True,
        )
        lab3.translate(fxw(0.05), fxh(0.30))
        # lowest
        lowest = T.translate("menu_party_level_lowest")
        lab4: Any = menu.add.label(
            title=f"{lowest}: {level_lowest or 0}",
            font_size=self.font_type.smaller,
            align=ALIGN_LEFT,
            float=True,
        )
        lab4.translate(fxw(0.05), fxh(0.35))
        # alignment
        if party_alignment:
            alignment = T.translate("menu_party_alignment")
            lab7: Any = menu.add.label(
                title=f"{alignment}: {T.translate(party_alignment)}",
                font_size=self.font_type.smaller,
                align=ALIGN_LEFT,
                float=True,
            )
            lab7.translate(fxw(0.05), fxh(0.40))

        total = sum(monster.steps for monster in monsters)
        # bond
        if self.char.bag.find_item("friendship_scroll"):
            lab5: Any = menu.add.label(
                title=T.translate("menu_bond"),
                font_size=self.font_type.big,
                align=ALIGN_LEFT,
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
                        align=ALIGN_LEFT,
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
                    unit_walked = U_KM
                else:
                    walked = formula.convert_mi(steps)
                    unit_walked = U_MI
                # labels
                params = {
                    "name": monster.name.upper(),
                    "walked": walked,
                    "unit": unit_walked,
                }
                lab6: Any = menu.add.label(
                    title=T.format("menu_party_traveled", params),
                    font_size=self.font_type.smaller,
                    align=ALIGN_LEFT,
                )
                lab6.translate(fxw(0.35), fxh(0.25))

    def process_event(self, event: PlayerInput) -> PlayerInput | None:
        params = {"character": self.char}
        if event.button == buttons.LEFT and event.pressed:
            self.client.replace_state("CharacterState", **params)
        if (
            event.button in (buttons.BACK, buttons.B, buttons.A)
            and event.pressed
        ):
            self.client.remove_state_by_name("PartyState")
        return None
