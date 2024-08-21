# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging

from tuxemon.db import MonsterEvolutionItemModel, StatType
from tuxemon.event import MapCondition, get_npc
from tuxemon.event.eventcondition import EventCondition
from tuxemon.monster import Monster
from tuxemon.session import Session
from tuxemon.tools import compare

logger = logging.getLogger(__name__)


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

        self.character = character
        self.client = session.client

        evolving_monsters = []
        for monster in character.monsters:
            if monster.evolutions:
                for evolution in monster.evolutions:
                    if self.can_evolve(monster, evolution):
                        evolved_monster = Monster()
                        evolved_monster.load_from_db(evolution.monster_slug)
                        evolving_monsters.append((monster, evolved_monster))

        if evolving_monsters:
            character.pending_evolutions = evolving_monsters

        return len(evolving_monsters) > 0

    def can_evolve(
        self, monster: Monster, evo: MonsterEvolutionItemModel
    ) -> bool:
        # Check if the evolution is actually possible
        if evo.monster_slug == monster.slug:
            return False

        conditions = [
            bool(
                evo.at_level
                and compare("greater_or_equal", monster.level, evo.at_level)
            ),
            bool(evo.gender and evo.gender == monster.gender),
            bool(evo.element and monster.has_type(evo.element)),
            bool(evo.tech and self.character.has_tech(evo.tech)),
            bool(evo.inside and evo.inside == self.client.map_inside),
            bool(evo.traded and evo.traded == monster.traded),
        ]

        # Check if the monster's stats meet the evolution conditions
        if evo.stats:
            params = evo.stats.split(":")
            operator = params[1]
            stat1 = monster.return_stat(StatType(params[0]))
            stat2 = monster.return_stat(StatType(params[2]))
            conditions.append(compare(operator, stat1, stat2))

        # Check if the monster's game variables meet the evolution conditions
        if evo.variable:
            parts = evo.variable.split(":")
            key, value = parts[:2]
            conditions.append(
                key in self.character.game_variables
                and self.character.game_variables[key] == value
            )

        # Check if the monster has taken the required number of steps
        if evo.steps:
            result = evo.steps - int(monster.steps)
            conditions.append(result == 0)
            monster.steps += 1
            monster.levelling_up = True
            monster.got_experience = True

        # Check if the monster's bond meets the evolution conditions
        if evo.bond:
            parts = evo.bond.split(":")
            operator, value = parts[:2]
            _bond = monster.bond
            conditions.append(compare(operator, _bond, int(value)))

        # If the evolution requires an item, do not evolve
        if evo.item:
            return False
        # The monster can evolve if any of the conditions are met
        return any(conditions)
