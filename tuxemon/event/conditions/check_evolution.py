# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass

from tuxemon.event import MapCondition, get_npc
from tuxemon.event.eventcondition import EventCondition
from tuxemon.monster import Monster
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
        _character = condition.parameters[0]
        character = get_npc(session, _character)
        if character is None:
            logger.error(f"{_character} not found")
            return False

        context = {
            "map_inside": session.client.map_manager.map_inside,
            "use_item": False,
        }

        evolving_monsters = []
        for monster in character.monsters:
            if monster.evolutions:
                for evolution in monster.evolutions:
                    if monster.evolution_handler.can_evolve(
                        evolution_item=evolution, context=context
                    ):
                        evolved_monster = Monster()
                        evolved_monster.load_from_db(evolution.monster_slug)
                        evolving_monsters.append((monster, evolved_monster))

        if evolving_monsters:
            character.pending_evolutions = evolving_monsters

        return len(evolving_monsters) > 0
