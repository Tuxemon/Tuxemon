# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from tuxemon.entity.path.commands import (
    ContinueCommand,
    MovementCommand,
    RepathCommand,
    StopMovementCommand,
)
from tuxemon.map.map import get_direction

if TYPE_CHECKING:
    from tuxemon.entity.npc import NPC
    from tuxemon.npc_manager import NPCManager


logger = logging.getLogger(__name__)


class ReroutePolicy:
    """
    Handles obstruction logic and rerouting decisions by returning commands.
    """

    def on_obstruction(
        self,
        owner: NPC,
        npc_manager: NPCManager,
        pathfinding: tuple[int, int] | None,
        target: tuple[int, int],
    ) -> list[MovementCommand]:

        commands: list[MovementCommand] = []

        if pathfinding:
            obstacle = npc_manager.get_entity_pos(target)

            if obstacle:
                # Immediate repath around dynamic obstruction (e.g., player)
                commands.append(
                    RepathCommand(
                        destination=pathfinding,
                        cooldown=0.5,
                        immediate=True,
                    )
                )
                return commands

            # Static obstruction → delayed repath + stop
            commands.append(
                RepathCommand(
                    destination=pathfinding,
                    cooldown=1.0,
                    immediate=False,
                )
            )
            commands.append(StopMovementCommand())
            return commands

        # No pathfinding active → simple obstruction
        commands.append(StopMovementCommand())
        return commands


class GhostReroutePolicy(ReroutePolicy):
    """
    Ghosts ignore walls and NPCs blocking the next tile.
    They only wait if the *final destination* is occupied.
    """

    def on_obstruction(
        self,
        owner: NPC,
        npc_manager: NPCManager,
        pathfinding: tuple[int, int] | None,
        target: tuple[int, int],
    ) -> list[MovementCommand]:

        commands: list[MovementCommand] = []

        if pathfinding:
            # Ghosts only care about the FINAL destination
            npc = npc_manager.get_entity_pos(pathfinding)
            if npc:
                commands.append(
                    RepathCommand(
                        destination=pathfinding,
                        cooldown=2.0,
                        immediate=False,
                    )
                )
                commands.append(StopMovementCommand())
                return commands

        # Otherwise ghosts phase through anything
        direction = get_direction(owner.tile_pos, target)
        commands.append(ContinueCommand(direction))
        return commands
