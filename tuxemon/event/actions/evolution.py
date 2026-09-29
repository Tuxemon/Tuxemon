# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, final
from uuid import UUID

from tuxemon.event.eventaction import EventAction
from tuxemon.monster.monster import Monster
from tuxemon.tools import get_valid_uuid

if TYPE_CHECKING:
    from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class EvolutionAction(EventAction):
    """
    Checks, asks and evolves.

    Script usage:
        .. code-block::

            evolution <character>

    Script parameters:
        character: Either "player" or npc slug name (e.g. "npc_maple").
        variable: Name of the variable where to store the monster id. If no
            variable is specified, all monsters get experience.
        evolution: Slug of the evolution.
    """

    name = "evolution"
    npc_slug: str
    variable: str | None = None
    evolution: str | None = None

    def start(self, session: Session) -> None:
        self.session = session
        self.client = session.client
        character = session.client.get_npc(self.npc_slug)

        if character is None:
            logger.error(f"{self.npc_slug} not found")
            self.stop()
            return

        self.char = character

        if self.client.has_extra_states():
            self.stop()
            return

        self._pending_map: dict[UUID, str] = {}

        if self.variable is None and self.evolution is None:
            self.process_pending_evolutions()
        elif self.variable is not None and self.evolution is not None:
            self.process_direct_evolutions(self.variable, self.evolution)
        else:
            raise ValueError(
                "Both variable and evolution must be either None or not None"
            )

    def process_direct_evolutions(self, variable: str, evolution: str) -> None:
        """Process direct evolutions for the character"""
        monster_id = get_valid_uuid(self.char.game_variables, variable)
        if monster_id is None:
            logger.info(f"No valid monster selected for variable '{variable}'")
            self.stop()
            return  # Exit early if no valid UUID

        monster = self.client.get_monster_by_iid(monster_id)

        if monster is None:
            logger.error(f"Monster '{monster_id}' doesn't exist.")
            self.stop()
            return

        if not monster.evolution_handler.is_valid_evolution_target(evolution):
            logger.error(
                f"Monster '{evolution}' isn't in the evolutionary path."
            )
            self.stop()
            return

        evolved = Monster.spawn_base(evolution, monster.level)
        evolved.transfer_properties_from(monster)
        monster.evolution_handler.evolve_monster(evolved)
        self.client.push_state(
            "EvolutionTransition", original=monster.slug, evolved=evolved.slug
        )

    def process_pending_evolutions(self) -> None:
        """Process pending evolutions for the character."""
        candidates = [m for m in self.char.monsters if m.waiting_to_evolve]
        if not candidates:
            self.stop()
            return

        monster = candidates[0]
        context = {"use_item": monster.waiting_to_evolve}
        slug = monster.evolution_handler.get_eligible_evolution_slug(context)

        if not slug:
            monster.waiting_to_evolve = False
            self.stop()
            return

        registry = self.char.evolution_registry
        if slug not in registry.get_pending(monster.instance_id):
            registry.add_pending(monster.instance_id, slug)

        evolved = Monster.spawn_base(slug, monster.level)
        evolved.transfer_properties_from(monster)

        self.client.push_state(
            "EvolutionState",
            monster=monster,
            target=evolved,
            character=self.char,
        )

    def update(self, session: Session, dt: float) -> None:
        if "EvolutionState" not in session.client.active_state_names:
            self.stop()
