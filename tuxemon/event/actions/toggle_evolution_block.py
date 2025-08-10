# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, final
from uuid import UUID

from tuxemon.event import get_monster_by_iid, get_npc
from tuxemon.event.eventaction import EventAction

if TYPE_CHECKING:
    from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class ToggleEvolutionBlockAction(EventAction):
    """
    Blocks or unblocks a specific evolution for a monster.

    Script usage:
        .. code-block::

            toggle_evolution_block <character> <monster_variable> <evolution_slug> <action>

    Script parameters:
        character: Either "player" or npc slug name (e.g. "npc_maple").
        monster_variable: Name of the variable storing the monster's instance ID.
        evolution_slug: The slug of the evolution to block/unblock.
        action: "block" to permanently block, "unblock" to unblock.
    """

    name = "toggle_evolution_block"
    npc_slug: str
    monster_variable: str
    evolution_slug: str
    action: str  # "block" or "unblock"

    def start(self, session: Session) -> None:
        self.session = session
        character = get_npc(session, self.npc_slug)

        if character is None:
            logger.error(f"Character '{self.npc_slug}' not found.")
            return

        registry = character.evolution_registry

        if self.monster_variable not in character.game_variables:
            logger.error(
                f"Variable '{self.monster_variable}' not found in {self.npc_slug}'s game variables."
            )
            return

        try:
            monster_id = UUID(character.game_variables[self.monster_variable])
        except ValueError:
            logger.error(
                f"Invalid UUID in variable '{self.monster_variable}': {character.game_variables[self.monster_variable]}"
            )
            return

        monster = get_monster_by_iid(self.session, monster_id)
        if monster is None:
            logger.warning(
                f"Monster with ID '{monster_id}' not found. Cannot toggle evolution block."
            )
            return

        if self.action == "block":
            registry.block_evolution_forever(monster_id, self.evolution_slug)
            logger.info(
                f"Evolution '{self.evolution_slug}' for monster {monster_id} ({monster.name}) has been permanently blocked."
            )
        elif self.action == "unblock":
            registry.unblock_evolution(monster_id, self.evolution_slug)
            logger.info(
                f"Evolution '{self.evolution_slug}' for monster {monster_id} ({monster.name}) has been unblocked."
            )
        else:
            raise ValueError(
                f"Invalid action '{self.action}' must be 'block' or 'unblock'."
            )
