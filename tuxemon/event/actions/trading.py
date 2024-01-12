# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import final

from tuxemon import formula
from tuxemon.db import SeenStatus
from tuxemon.event.eventaction import EventAction
from tuxemon.monster import Monster


@final
@dataclass
class TradingAction(EventAction):
    """
    Select a monster in the player party and trade.

    Script usage:
        .. code-block::

            trading <removed>,<added>

    Script parameters:
        removed: Instance id (name variable).
        added: Slug monster.

    """

    name = "trading"
    removed: str
    added: str

    def switch_monster(self, removed: Monster) -> None:
        slot = self.player.monsters.index(removed)
        # creates traded monster
        added = Monster()
        added.load_from_db(self.added)
        added.set_level(removed.level)
        added.set_moves(removed.level)
        added.set_capture(formula.today_ordinal())
        added.current_hp = added.hp
        added.traded = True
        # switch
        self.player.remove_monster(removed)
        self.player.add_monster(added, slot)
        self.player.tuxepedia[self.added] = SeenStatus.caught

    def start(self) -> None:
        self.player = self.session.player
        iid = uuid.UUID(self.player.game_variables[self.removed])
        removed = self.player.find_monster_by_id(iid)
        if removed:
            self.switch_monster(removed)
