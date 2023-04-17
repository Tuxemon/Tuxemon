# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, final

from tuxemon import prepare
from tuxemon.event.eventaction import EventAction
from tuxemon.states.world.worldstate import WorldState


@final
@dataclass
class TeleportAction(EventAction):
    """
    Teleport the player to a particular map and tile coordinates.

    Script usage:
        .. code-block::

            teleport <map_name>,<x>,<y>

    Script parameters:
        map_name: Name of the map to teleport to.
        x: X coordinate of the map to teleport to.
        y: Y coordinate of the map to teleport to.

    """

    name = "teleport"
    map_name: str
    x: int
    y: int
    # This value is unused, but in too many places to remove right now
    _: Optional[float] = None

    def start(self) -> None:
        player = self.session.player
        world = self.session.client.get_state_by_name(WorldState)

        # If we're doing a screen transition with this teleport, set the map
        # name that we'll load during the apex of the transition.
        # TODO: This only needs to happen once.
        if world.in_transition:
            world.delayed_mapname = self.map_name

        # Check to see if we're also performing a transition. If we are, wait
        # to perform the teleport at the apex of the transition
        if world.in_transition:
            # the world state will handle the teleport/transition, hopefully
            world.delayed_teleport = True
            world.delayed_x = self.x
            world.delayed_y = self.y

        else:
            # If we're not doing a transition, then just do the teleport
            map_path = prepare.fetch("maps", self.map_name)

            if world.current_map is None:
                world.change_map(map_path)

            elif map_path != world.current_map.filename:
                world.change_map(map_path)

            # Stop the player's movement so they don't continue their move
            # after they teleported.
            player.cancel_path()

            # must change position after the map is loaded
            player.set_position((self.x, self.y))

            # unlock_controls will reset controls, but start moving if keys
            # are pressed
            world.unlock_controls()
