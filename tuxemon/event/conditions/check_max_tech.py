# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass

from tuxemon.db import SpatialCondition
from tuxemon.event import get_npc
from tuxemon.event.eventcondition import EventCondition
from tuxemon.monster import Monster
from tuxemon.prepare import MAX_MOVES
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@dataclass
class CheckMaxTechCondition(EventCondition):
    """
    Condition to check whether a character (player or NPC) has at least one
    Tuxemon with more techniques than a specified threshold.

    This condition is used in event scripting to trigger actions based on
    the number of techniques a Tuxemon possesses. If the condition is met,
    the matching monsters are stored in the session's `event_data` dictionary
    under the key `"check_max_tech"`.

    Script usage:
        .. code-block::

            is check_max_tech <character>[,nr]

    Script parameters:
        character: Either "player" or NPC slug name (e.g. "npc_maple").
        nr: Optional integer specifying the minimum number of techniques.
            Defaults to the constant MAX_MOVES.

    Examples:
        - "is check_max_tech player"
        - "is check_max_tech npc_maple,2"
    """

    name = "check_max_tech"

    def test(self, session: Session, condition: SpatialCondition) -> bool:
        target_name = condition.parameters[0]

        target_character = get_npc(session, target_name)
        if target_character is None:
            logger.error(f"Character '{target_name}' not found.")
            return False

        try:
            max_techs = (
                int(condition.parameters[1])
                if len(condition.parameters) > 1
                else MAX_MOVES
            )
        except ValueError:
            logger.error(
                f"Invalid technique threshold: {condition.parameters[1]}"
            )
            return False

        logger.debug(f"Technique threshold set to: {max_techs}")

        matching_monsters: list[Monster] = []
        for monster in target_character.monsters:
            num_moves = len(monster.moves.current_moves)
            logger.debug(
                f"Checking monster: {monster.name} (ID: {monster.instance_id}) with {num_moves} moves"
            )

            if num_moves > max_techs:
                logger.debug(
                    f"  Monster '{monster.name}' exceeds technique threshold"
                )
                matching_monsters.append(monster)

        session.client.event_data[self.name] = matching_monsters
        logger.debug(
            f"Matching monsters stored: {[m.name for m in matching_monsters]}"
        )

        return bool(matching_monsters)
