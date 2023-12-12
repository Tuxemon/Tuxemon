# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.db import Direction
from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.map import get_direction
from tuxemon.states.world.worldstate import WorldState


@final
@dataclass
class CharFaceAction(EventAction):
    """
    Make the character face a certain direction.

    Script usage:
        .. code-block::

            char_face <character>,<direction>

    Script parameters:
        character: Either "player" or character slug name (e.g. "npc_maple").
        direction: Direction to face. It can be: "left", "right", "up", "down",
             "player" or a character slug.

    """

    name = "char_face"
    character: str
    direction: str

    def start(self) -> None:
        character = get_npc(self.session, self.character)
        assert character

        # "player" isn't among the Directions (map_loader.py)
        if self.direction not in list(Direction):
            target = get_npc(self.session, self.direction)
            assert target
            direction = get_direction(character.tile_pos, target.tile_pos)
        else:
            direction = Direction(self.direction)

        # If we're doing a transition, only change the player's facing when
        # we've reached the apex of the transition.
        if character.isplayer:
            world_state = self.session.client.get_state_by_name(WorldState)
            if world_state.in_transition:
                world_state.delayed_facing = direction
            else:
                character.facing = direction
        else:
            character.facing = direction
