# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging

from tuxemon.db import StatType
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

        client = session.client
        _evolution: bool = False

        evolving: list[tuple[Monster, Monster]] = []
        for monster in character.monsters:
            if monster.evolutions:
                evolved = Monster()
                for evolution in monster.evolutions:
                    evolved.load_from_db(evolution.monster_slug)
                    op = "greater_or_equal"
                    if compare(op, monster.level, evolution.at_level):
                        _evolution = True
                    if evolution.gender == monster.gender:
                        _evolution = True
                    if character.has_type(evolution.element):
                        _evolution = True
                    if character.has_tech(evolution.tech):
                        _evolution = True
                    if evolution.inside == client.map_inside:
                        _evolution = True
                    if evolution.traded == monster.traded:
                        _evolution = True
                    if evolution.stats:
                        params = evolution.stats.split(":")
                        operator = params[1]
                        stat1 = monster.return_stat(StatType(params[0]))
                        stat2 = monster.return_stat(StatType(params[2]))
                        _evolution = compare(operator, stat1, stat2)
                    if evolution.variable:
                        parts = evolution.variable.split(":")
                        key, value = parts[:2]
                        if (
                            key in character.game_variables
                            and character.game_variables[key] == value
                        ):
                            _evolution = True
                    if evolution.steps:
                        result = evolution.steps - int(monster.steps)
                        if result == 0:
                            _evolution = True
                            monster.steps += 1
                        monster.levelling_up = True
                        monster.got_experience = True
                    if evolution.bond:
                        parts = evolution.bond.split(":")
                        operator, value = parts[:2]
                        _evolution = compare(operator, monster.bond, value)
                    # use the item on the monster
                    if evolution.item:
                        _evolution = False
                    if _evolution:
                        evolving.append((monster, evolved))

        if evolving:
            character.pending_evolutions = evolving
        return len(evolving) > 0
