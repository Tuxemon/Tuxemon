# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, final

from tuxemon.event.eventaction import EventAction
from tuxemon.tools import get_valid_uuid

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
        character = session.client.get_npc(self.npc_slug)

        if character is None:
            logger.error(f"Character '{self.npc_slug}' not found.")
            self.stop()
            return

        registry = character.evolution_registry

        monster_id = get_valid_uuid(
            character.game_variables, self.monster_variable
        )
        if monster_id is None:
            logger.info(
                f"No valid monster selected for variable '{self.monster_variable}'"
            )
            self.stop()
            return  # Exit early if no valid UUID

        monster = session.client.get_monster_by_iid(monster_id)
        if monster is None:
            logger.warning(
                f"Monster with ID '{monster_id}' not found. Cannot toggle evolution block."
            )
            self.stop()
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
