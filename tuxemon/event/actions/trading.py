# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import final

from tuxemon import formula
from tuxemon.db import SeenStatus
from tuxemon.event.eventaction import EventAction
from tuxemon.menu.interface import MenuItem
from tuxemon.monster import Monster
from tuxemon.states.monster import MonsterMenuState


@final
@dataclass
class TradingAction(EventAction):
    """
    Select a monster in the player party and trade.

    Script usage:
        .. code-block::

            trading <remove_monster>,<add_monster>

    Script parameters:
        remove_monster: Slug monster.
        add_monster: Slug monster.

    """

    name = "trading"
    remove: str
    add: str

    def set_var(self, menu_item: MenuItem[Monster]) -> None:
        if menu_item.game_object.slug == self.remove:
            self.player.game_variables["trading_monster"] = str(
                menu_item.game_object.instance_id.hex
            )
            self.switch_monster()

    def switch_monster(self) -> None:
        trading_id = uuid.UUID(self.player.game_variables["trading_monster"])
        trading = self.player.find_monster_by_id(trading_id)
        if trading is None:
            raise ValueError(
                f"Could not find monster with instance id {trading_id}"
            )
        slot = self.player.monsters.index(trading)
        new = Monster()
        new.load_from_db(self.add)
        new.set_level(trading.level)
        new.set_moves(trading.level)
        new.set_capture(formula.today_ordinal())
        new.current_hp = new.hp
        self.player.remove_monster(trading)
        self.player.add_monster(new, slot)
        self.player.tuxepedia[self.add] = SeenStatus.caught
        self.session.client.pop_state()

    def start(self) -> None:
        self.player = self.session.player

        # pull up the monster menu
        old = self.player.find_monster(self.remove)
        if old is not None:
            menu = self.session.client.push_state(MonsterMenuState())
            menu.on_menu_selection = self.set_var  # type: ignore[assignment]
        else:
            raise ValueError(
                f"{self.remove} isn't in your party.\n"
                "Advice: use the condition has_monster\n"
                "or monster_property to avoid issues."
            )

    def update(self) -> None:
        try:
            self.session.client.get_state_by_name(MonsterMenuState)
        except ValueError:
            self.stop()
