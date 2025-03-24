# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Callable
from typing import Any, Optional

import pygame_menu
from pygame_menu import locals

from tuxemon import formula
from tuxemon import prepare as pre
from tuxemon.db import MonsterModel, OutputBattle, db
from tuxemon.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.npc import NPC
from tuxemon.platform.const import buttons
from tuxemon.platform.events import PlayerInput
from tuxemon.time_handler import today_ordinal

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


class CharacterState(PygameMenuState):
    """
    This state is responsible for the character menu.

    By clicking right, it gives access to the Party Menu.

    Shows details of the character (e.g. monster captured, seen,
    battles, wallet, etc.).

    """

    def add_menu_items(
        self,
        menu: pygame_menu.Menu,
    ) -> None:
        width = menu._width
        height = menu._height

        name = (
            T.translate(self.char.slug)
            if self.char.name == ""
            else self.char.name
        )

        player = "player" if self.char.isplayer else self.char.slug

        # tuxepedia data
        filters = list(lookup_cache.values())
        completeness = self.char.tuxepedia.get_completeness(len(filters))
        percentage = round(completeness * 100, 1)
        seen = self.char.tuxepedia.get_seen_count()
        caught = self.char.tuxepedia.get_caught_count()

        if self.char.tuxepedia.entries:
            _msg_progress = {"value": str(percentage)}
            _msg_seen = {"param": str(seen + caught), "all": str(len(filters))}
            _msg_caught = {"param": str(caught), "all": str(len(filters))}
        else:
            _msg_progress = {"value": "-"}
            _msg_seen = {"param": "-", "all": "-"}
            _msg_caught = {"param": "-", "all": "-"}

        msg_progress = T.format("tuxepedia_progress", _msg_progress)
        msg_seen = T.format("tuxepedia_data_seen", _msg_seen)
        msg_caught = T.format("tuxepedia_data_caught", _msg_caught)

        today = today_ordinal()
        date = self.char.game_variables.get("date_start_game", today)
        date_begin = today - int(date)
        msg_begin = (
            T.format("player_start_adventure", {"date": date_begin})
            if date_begin >= 1
            else T.translate("player_start_adventure_today")
        )

        battle_outcomes = {
            OutputBattle.won: 0,
            OutputBattle.lost: 0,
            OutputBattle.draw: 0,
        }

        for battle in self.char.battles:
            if battle.fighter == player:
                battle_outcomes[battle.outcome] += 1

        tot = sum(battle_outcomes.values())
        won = battle_outcomes[OutputBattle.won]
        lost = battle_outcomes[OutputBattle.lost]
        draw = battle_outcomes[OutputBattle.draw]

        _msg_battles = {
            "tot": str(tot),
            "won": str(won),
            "draw": str(draw),
            "lost": str(lost),
        }
        msg_battles = T.format("player_battles", _msg_battles)
        # steps
        steps = self.char.steps
        unit = self.client.config.unit_measure
        if unit == "metric":
            walked = formula.convert_km(steps)
            unit_walked = pre.U_KM
        else:
            walked = formula.convert_mi(steps)
            unit_walked = pre.U_MI
        _msg_walked = {"distance": str(walked), "unit": unit_walked}
        msg_walked = T.format("player_walked", _msg_walked)
        # name
        menu._auto_centering = False
        lab1: Any = menu.add.label(
            title=name.upper(),
            label_id="name",
            font_size=self.font_size_big,
            align=locals.ALIGN_LEFT,
            underline=True,
            float=True,
        )
        lab1.translate(fix_measure(width, 0.45), fix_measure(height, 0.15))
        # money
        money = self.char.money_controller.money_manager.get_money()
        lab2: Any = menu.add.label(
            title=f"{T.translate('wallet')}: {money}",
            label_id="money",
            font_size=self.font_size_smaller,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        lab2.translate(fix_measure(width, 0.45), fix_measure(height, 0.25))
        # seen
        lab3: Any = menu.add.label(
            title=msg_seen,
            label_id="seen",
            font_size=self.font_size_smaller,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        lab3.translate(fix_measure(width, 0.45), fix_measure(height, 0.30))
        # caught
        lab4: Any = menu.add.label(
            title=msg_caught,
            label_id="caught",
            font_size=self.font_size_smaller,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        lab4.translate(fix_measure(width, 0.45), fix_measure(height, 0.35))
        # begin adventure
        lab5: Any = menu.add.label(
            title=msg_begin,
            label_id="begin",
            font_size=self.font_size_smaller,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        lab5.translate(fix_measure(width, 0.45), fix_measure(height, 0.40))
        # walked
        if steps > 0.0:
            lab6: Any = menu.add.label(
                title=msg_walked,
                label_id="walked",
                font_size=self.font_size_smaller,
                align=locals.ALIGN_LEFT,
                float=True,
            )
            lab6.translate(fix_measure(width, 0.45), fix_measure(height, 0.45))
        # battles
        lab7: Any = menu.add.label(
            title=msg_battles,
            label_id="battle",
            font_size=self.font_size_smaller,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        lab7.translate(fix_measure(width, 0.45), fix_measure(height, 0.50))
        # % tuxepedia
        lab8: Any = menu.add.label(
            title=msg_progress,
            label_id="progress",
            font_size=self.font_size_smaller,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        lab8.translate(fix_measure(width, 0.45), fix_measure(height, 0.10))
        # image
        combat_front = self.char.template.combat_front
        _path = f"gfx/sprites/player/{combat_front}.png"
        new_image = self._create_image(_path)
        new_image.scale(pre.SCALE, pre.SCALE)
        image_widget = menu.add.image(image_path=new_image.copy())
        image_widget.set_float(origin_position=True)
        image_widget.translate(
            fix_measure(width, 0.20), fix_measure(height, 0.08)
        )

    def __init__(self, **kwargs: Any) -> None:
        if not lookup_cache:
            _lookup_monsters()
        character: Optional[NPC] = None
        for element in kwargs.values():
            character = element["character"]
        if character is None:
            raise ValueError("No character found")
        width, height = pre.SCREEN_SIZE

        self.char = character

        bg = (
            pre.BG_PLAYER2
            if self.char.monsters and self.char.isplayer
            else pre.BG_PLAYER1
        )

        theme = self._setup_theme(bg)
        theme.scrollarea_position = locals.POSITION_EAST
        theme.widget_alignment = locals.ALIGN_CENTER

        super().__init__(height=height, width=width)

        self.add_menu_items(self.menu)
        self.reset_theme()

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        party = self.char.monsters
        if event.button == buttons.RIGHT and event.pressed and party:
            params = {"party": party}
            self.client.replace_state("PartyState", kwargs=params)
        if (
            event.button in (buttons.BACK, buttons.B, buttons.A)
            and event.pressed
        ):
            self.client.pop_state()
        return None
