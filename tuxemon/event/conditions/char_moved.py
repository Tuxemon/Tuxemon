# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from tuxemon.event import MapCondition, collide, get_npc
from tuxemon.event.eventcondition import EventCondition
from tuxemon.event.eventpersist import EventPersist
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
        return generic_test(
            self.name, session.client.event_persist, condition, character
        )


def generic_test(
    name: str, persist: EventPersist, condition: MapCondition, character: NPC
) -> bool:
    """
    Determine if a character has moved onto an event tile.

    Parameters:
        name: The unique identifier for the event condition.
        persist: The event persistence object used to track state changes.
        condition: The event condition being evaluated.
        character: The character whose movement is being assessed.

    Returns:
        True if the character has moved onto the event tile, False otherwise.
    """
    # Retrieve where the character is going (not where it currently is)
    move_destination = character.move_destination

    # Create a unique identifier for the condition (hash/id of sorts)
    condition_str = str(condition)

    stopped = move_destination is None
    collide_next = False
    if move_destination is not None:
        collide_next = collide(condition, move_destination)

    # Retrieve persistent storage where movement tracking data is stored
    stored = persist.get_event_data(name)

    # Get the last recorded destination for this specific condition
    last_destination: Optional[tuple[int, int]] = stored.get(condition_str)

    # If no last destination is recorded, update storage when movement stops or collides
    if last_destination is None and (stopped or collide_next):
        persist.update_event_data(name, condition_str, move_destination)

    # Check whether the character's move destination has changed since the last frame
    moved = move_destination != last_destination

    # Verify if the character is currently colliding with the condition boundaries
    collided = collide(condition, character.tile_pos)

    # Update movement tracking data for this condition
    persist.update_event_data(name, condition_str, move_destination)

    # If the character moved into the tile AND previously had a recorded position,
    # trigger the event
    if collided and moved and last_destination is not None:
        # Reset tracking to ensure the condition triggers only once
        persist.update_event_data(name, condition_str, None)
        return True

    return False
