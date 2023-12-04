# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from tuxemon.event import MapCondition, collide
from tuxemon.event.eventcondition import EventCondition
from tuxemon.npc import NPC
from tuxemon.session import Session


class PlayerMovedCondition(EventCondition):
    """
    Check to see the player has just moved into this tile.

    Using this condition will prevent a condition like "player_at" from
    constantly being true every single frame.

    * Check if player destination collides with event
    * If it collides, wait until destination changes
    * Become True after collides and destination has changed

    These rules ensure that the event is true once player in the tile
    and is only true once.  Could possibly be better, IDK.

    Script usage:
        .. code-block::

            is player_moved

    """

    name = "player_moved"

    def test(self, session: Session, condition: MapCondition) -> bool:
        """
        Check to see the player has just moved into this tile.

        Parameters:
            session: The session object
            condition: The map condition object.

        Returns:
            Whether the player has just moved to the position.

        """
        # TODO: Eventually generalize command for checking players and npcs
        return self.generic_test(session, condition, session.player)

    def generic_test(
        self,
        session: Session,
        condition: MapCondition,
        npc: NPC,
    ) -> bool:
        """
        Check to see if a character has just moved into this tile.

        Parameters:
            session: The session object
            condition: The map condition object.
            npc: The character to test for.

        Returns:
            Whether the character has just moved to the position.

        """
        # check where the npc is going, not where it is
        move_destination = npc.move_destination

        # a hash/id of sorts for the condition
        condition_str = str(condition)

        stopped = move_destination is None
        collide_next = False
        if move_destination is not None:
            collide_next = collide(condition, move_destination)

        # persist is data shared for all player_moved EventConditions
        persist = self.get_persist(session)

        # only test if tile was moved into
        # get previous destination for this particular condition
        last_destination = persist.get(condition_str)
        if last_destination is None and (stopped or collide_next):
            persist[condition_str] = move_destination

        # has the npc moved onto or away from the event?
        # Check to see if the npc's "move destination" has changed since the
        # last frame. If it has, WE'RE MOVING!!!
        moved = move_destination != last_destination

        # is the npc colliding with the condition boundaries?
        collided = collide(condition, npc.tile_pos)

        # Update the current npc's last move destination
        # TODO: some sort of global tracking of player instead of recording it
        # in conditions
        persist[condition_str] = move_destination

        # determine if the tile has truly changed
        if collided and moved and last_destination is not None:
            persist[condition_str] = None
            return True
        return False
