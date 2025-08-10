# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass

from tuxemon.event import MapCondition, get_npc
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@dataclass
class CheckEvolutionCondition(EventCondition):
    """
    Check to see the player has at least one tuxemon evolving.
    If yes, it'll save the monster and the evolution inside a list.
    The list will be used by the event action "evolution".

    Script usage:
        .. code-block::

            is check_evolution <character>

    Script parameters:
        character: Either "player" or npc slug name (e.g. "npc_maple").

    eg. "is check_evolution player"
    """

    name = "check_evolution"

    def test(self, session: Session, condition: MapCondition) -> bool:
        target_name = condition.parameters[0]
        logger.debug(
            f"EvolutionCondition.test() called with target_name='{target_name}'"
        )

        target_character = get_npc(session, target_name)
        if target_character is None:
            logger.error(f"Character '{target_name}' not found.")
            return False

        logger.debug(f"Found character: {target_character.name}")
        context = {"map_inside": session.client.map_manager.map_inside}
        new_evolutions_found = False
        has_pending_evolutions = False

        for monster in target_character.monsters:
            logger.debug(
                f"Checking monster: {monster.name} (ID: {monster.instance_id})"
            )

            if not monster.evolutions:
                logger.debug(f"  No evolutions available for {monster.name}")
                continue

            registry = target_character.evolution_registry
            pending_evolutions = registry.get_pending(monster.instance_id)
            blocked_evolutions = registry.get_blocked(monster.instance_id)

            if pending_evolutions:
                logger.debug(
                    f"  Already has pending evolutions: {pending_evolutions}"
                )
                has_pending_evolutions = True

            for evolution_data in monster.evolutions:
                evolution_slug = evolution_data.monster_slug
                logger.debug(
                    f"  Evaluating evolution option: {evolution_slug}"
                )

                if evolution_slug in blocked_evolutions:
                    logger.debug(
                        f"  Skipping '{evolution_slug}' — permanently blocked"
                    )
                    continue

                if evolution_slug in pending_evolutions:
                    logger.debug(
                        f"  Skipping '{evolution_slug}' — already pending"
                    )
                    continue

                if monster.evolution_handler.can_evolve(
                    evolution_item=evolution_data, context=context
                ):
                    logger.debug(f"  Adding '{evolution_slug}' to pending")
                    registry.add_pending(monster.instance_id, evolution_slug)
                    new_evolutions_found = True
                    has_pending_evolutions = True
                else:
                    logger.debug(
                        f"  '{evolution_slug}' not valid in current context"
                    )

        logger.debug(f"New evolutions found: {new_evolutions_found}")
        logger.debug(f"Has any pending evolutions: {has_pending_evolutions}")
        return has_pending_evolutions
