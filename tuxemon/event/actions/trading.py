# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import final

from tuxemon import formula
from tuxemon.db import SeenStatus, db
from tuxemon.event import get_monster_by_iid
from tuxemon.event.eventaction import EventAction
from tuxemon.monster import Monster

logger = logging.getLogger(__name__)


@final
@dataclass
class TradingAction(EventAction):
    """
    Select a monster in the player party and trade.

    Script usage:
        .. code-block::

            trading <variable>,<added>

    Script parameters:
        variable: Name of the variable where to store the monster id (removed).
        added: Slug monster or Name of the variable where to store the monster
            id (added).

    eg. "trading name_variable,apeoro"
    eg. "trading name_variable,name_variable"

    """

    name = "trading"
    variable: str
    added: str

    def create_monster(self, removed: Monster) -> None:
        # retrieves character from monster
        character = removed.owner
        if character is None:
            logger.error(f"{removed.name}'s owner not found!")
            return
        slot = character.monsters.index(removed)
        # creates traded monster
        added = Monster()
        added.load_from_db(self.added)
        added.set_level(removed.level)
        added.set_moves(removed.level)
        added.set_capture(formula.today_ordinal())
        added.current_hp = added.hp
        added.traded = True
        logger.info(f"{removed.name} traded for {added.name}!")
        # switch
        character.remove_monster(removed)
        character.add_monster(added, slot)
        character.tuxepedia[added.slug] = SeenStatus.caught

    def switch_monster(self, removed: Monster, added: Monster) -> None:
        # defines characters
        receiver = removed.owner
        giver = added.owner
        if receiver is None:
            logger.error(f"{removed.name}'s owner not found!")
            return
        if giver is None:
            logger.error(f"{added.name}'s owner not found!")
            return
        # retrieves slots
        slot_removed = receiver.monsters.index(removed)
        slot_added = giver.monsters.index(added)
        # set monsters as traded
        removed.traded = True
        added.traded = True
        # logger info
        logger.info(f"{removed.name} traded for {added.name}!")
        logger.info(f"{added.name} traded for {removed.name}!")
        logger.info(f"{receiver.name} welcomes {added.name}!")
        logger.info(f"{giver.name} welcomes {removed.name}!")
        # operations giver
        giver.remove_monster(removed)
        receiver.add_monster(added, slot_removed)
        receiver.tuxepedia[added.slug] = SeenStatus.caught
        # operations receiver
        receiver.remove_monster(added)
        giver.add_monster(removed, slot_added)
        giver.tuxepedia[removed.slug] = SeenStatus.caught

    def start(self) -> None:
        player = self.session.player
        _monster_id = uuid.UUID(player.game_variables[self.variable])
        monster_id = get_monster_by_iid(self.session, _monster_id)
        if monster_id is None:
            logger.error("Monster not found")
            return

        # checks monster slug exists
        if self.added not in list(db.database["monster"]):
            _added_id = uuid.UUID(player.game_variables[self.added])
            added_id = get_monster_by_iid(self.session, _added_id)
            if added_id is None:
                logger.error("Monster not found")
                return
            self.switch_monster(monster_id, added_id)
        else:
            self.create_monster(monster_id)
