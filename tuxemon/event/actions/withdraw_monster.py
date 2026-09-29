# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session
from tuxemon.tools import get_valid_uuid

logger = logging.getLogger(__name__)


@final
@dataclass
class WithdrawMonsterAction(EventAction):
    """
    Pull a monster from the given trainer's storage and puts it in their party.

    Note:
        If the trainer's party is already full then the monster will be
        deposited into the default storage box automatically.

    Script usage:
        .. code-block::

            withdraw_monster <variable>,<character>

    Script parameters:
        variable: Name of the variable where to store the monster id.
        character: Either "player" or npc slug name (e.g. "npc_maple").
            the one who is going to receive the monster
    """

    name = "withdraw_monster"
    variable: str
    character: str

    def start(self, session: Session) -> None:
        player = session.player

        monster_id = get_valid_uuid(player.game_variables, self.variable)
        if monster_id is None:
            logger.info(
                f"No valid monster selected for variable '{self.variable}'"
            )
            self.stop()
            return  # Exit early if no valid UUID
        monster = player.monster_boxes.get_monsters_by_iid(monster_id)
        if monster is None:
            logger.error("Monster not found")
            self.stop()
            return

        player.monster_boxes.remove_from_box("monster", None, monster)

        character = session.client.get_npc(self.character)
        if character is None:
            logger.error(f"{self.character} not found")
            self.stop()
            return

        if character.party.transfer_monster_to_party(monster):
            logger.info(
                f"{character.name} withdrew {monster.name} into party!"
            )
        else:
            if character.party.send_monster_to_box(monster):
                logger.info(
                    f"{character.name}'s party was full. {monster.name} sent to box instead."
                )
            else:
                logger.error(
                    f"Failed to withdraw monster '{monster.name}' from box"
                )
