# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import partial
from typing import TYPE_CHECKING, Optional, final
from uuid import UUID

from tuxemon.event import get_monster_by_iid, get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.locale import T
from tuxemon.monster import Monster
from tuxemon.tools import open_choice_dialog, open_dialog
from tuxemon.ui.menu_options import ChoiceOption, MenuOptions

if TYPE_CHECKING:
    from tuxemon.session import Session

logger = logging.getLogger(__name__)

MAX_ACTIVE_STATES: int = 2


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
    variable: Optional[str] = None
    evolution: Optional[str] = None

    def start(self, session: Session) -> None:
        self.session = session
        self.client = session.client
        character = get_npc(session, self.npc_slug)

        if character is None:
            logger.error(f"{self.npc_slug} not found")
            return

        self.char = character

        if len(self.client.state_manager.active_states) > MAX_ACTIVE_STATES:
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
        if variable not in self.char.game_variables:
            logger.error(f"Variable '{variable}' doesn't exist.")
            return

        monster_id = UUID(self.char.game_variables[variable])
        monster = get_monster_by_iid(self.session, monster_id)

        if monster is None:
            logger.error(f"Monster '{monster_id}' doesn't exist.")
            return

        if not monster.evolution_handler.has_evolution_to(
            evolution
        ) and not monster.evolution_handler.has_history_to(evolution):
            logger.error(
                f"Monster '{evolution}' isn't in the evolutionary path."
            )
            return

        evolved = Monster.create(evolution)
        monster.evolution_handler.evolve_monster(evolved)
        self.client.push_state(
            "EvolutionTransition", original=monster.slug, evolved=evolved.slug
        )

    def process_pending_evolutions(self) -> None:
        """Process pending evolutions for the character"""
        registry = self.char.evolution_registry
        logger.debug(
            f"Checking pending evolutions for character: {self.char.name}"
        )

        evolve_candidates: list[Monster] = []
        for monster in self.char.monsters:
            logger.debug(
                f"Evaluating monster: {monster.name} (ID: {monster.instance_id})"
            )
            logger.debug(
                f"  got_experience={monster.got_experience}, levelling_up={monster.levelling_up}"
            )

            pending = registry.get_pending(monster.instance_id)
            logger.debug(f"  Pending evolutions: {pending}")

            if monster.got_experience and monster.levelling_up and pending:
                evolve_candidates.append(monster)
                logger.debug(f"  -> Added to evolve_candidates")

        if not evolve_candidates:
            logger.debug("No evolve candidates found. Returning from action.")
            return

        monster_to_evolve = evolve_candidates[0]
        logger.debug(
            f"Selected monster for evolution: {monster_to_evolve.name}"
        )

        pending_evolutions = registry.get_pending(
            monster_to_evolve.instance_id
        )
        logger.debug(
            f"Pending evolutions for selected monster: {pending_evolutions}"
        )

        registry.clear_pending(monster_to_evolve.instance_id)
        logger.debug(
            f"Cleared pending evolutions for monster: {monster_to_evolve.name}"
        )

        slug = pending_evolutions[0]
        evolved = Monster.create(slug)
        logger.debug(f"Created evolved monster: {evolved.name} (slug: {slug})")

        self._pending_map[monster_to_evolve.instance_id] = slug
        logger.debug(f"Stored pending evolution slug for denial logic")

        self.question_evolution(monster_to_evolve, evolved)

    def question_evolution(self, monster: Monster, evolved: Monster) -> None:
        """Ask the user to confirm the evolution"""
        params = {
            "name": monster.name.upper(),
            "evolve": evolved.name.upper(),
        }
        msg = T.format("evolution_confirmation", params)
        open_dialog(self.session.client, [msg])

        options = [
            ChoiceOption(
                key="yes",
                display_text=T.translate("yes"),
                action=partial(self.confirm_evolution, monster, evolved),
            ),
            ChoiceOption(
                key="no",
                display_text=T.translate("no"),
                action=partial(self.deny_evolution, monster),
            ),
        ]

        open_choice_dialog(self.session.client, MenuOptions(options))

    def confirm_evolution(self, monster: Monster, evolved: Monster) -> None:
        """Confirm the evolution"""
        self.client.pop_state()
        self.client.pop_state()
        logger.info(f"{monster.name} evolves into {evolved.name}!")

        registry = self.char.evolution_registry
        registry.clear_missed(monster.instance_id, evolved.slug)
        registry.clear_pending(monster.instance_id)
        self._pending_map.pop(monster.instance_id, None)

        monster.evolution_handler.evolve_monster(evolved)
        self.client.push_state(
            "EvolutionTransition", original=monster.slug, evolved=evolved.slug
        )

    def deny_evolution(self, monster: Monster) -> None:
        """Deny the evolution"""
        monster.got_experience = False
        monster.levelling_up = False
        logger.info(f"{monster.name}'s evolution refused!")

        slug = self._pending_map.get(monster.instance_id)
        if slug:
            registry = self.char.evolution_registry
            registry.log_missed(monster.instance_id, slug, monster.level)
            registry.clear_pending(monster.instance_id)
            self._pending_map.pop(monster.instance_id, None)

        self.client.pop_state()
        self.client.pop_state()
