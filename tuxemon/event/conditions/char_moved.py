# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass

from tuxemon.event import MapCondition, collide, get_npc
from tuxemon.event.eventcondition import EventCondition
from tuxemon.npc import NPC
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@dataclass
class CharMovedCondition(EventCondition):
    """
    Check to see the player has just moved into this tile.

    Using this condition will prevent a condition like "char_at" from
    constantly being true every single frame.

    * Check if player destination collides with event
    * If it collides, wait until destination changes
    * Become True after collides and destination has changed

    These rules ensure that the event is true once player in the tile
    and is only true once.  Could possibly be better, IDK.

    Script usage:
        .. code-block::

            is char_moved <character>

    Script parameters:
        character: Either "player" or character slug name (e.g. "npc_maple")

    """

    name = "char_moved"

    def test(self, session: Session, condition: MapCondition) -> bool:
        character = get_npc(session, condition.parameters[0])
        if character is None:
            logger.error(f"{condition.parameters[0]} not found")
            return False
        return self.generic_test(session, condition, character)

    def generic_test(
        self,
        session: Session,
        condition: MapCondition,
        character: NPC,
    ) -> bool:
        # check where the character is going, not where it is
        move_destination = character.move_destination

        # a hash/id of sorts for the condition
        condition_str = str(condition)

        stopped = move_destination is None
        collide_next = False
        if move_destination is not None:
            collide_next = collide(condition, move_destination)

        # persist is data shared for all char_moved EventConditions
        persist = self.get_persist(session)

        # only test if tile was moved into
        # get previous destination for this particular condition
        last_destination = persist.get(condition_str)
        if last_destination is None and (stopped or collide_next):
            persist[condition_str] = move_destination

        # has the character moved onto or away from the event?
        # Check to see if the character's "move destination" has changed since the
        # last frame. If it has, WE'RE MOVING!!!
        moved = move_destination != last_destination

        # is the character colliding with the condition boundaries?
        collided = collide(condition, character.tile_pos)

        # Update the current character's last move destination
        # TODO: some sort of global tracking of player instead of recording it
        # in conditions
        persist[condition_str] = move_destination

        # determine if the tile has truly changed
        if collided and moved and last_destination is not None:
            persist[condition_str] = None
            return True
        return False
