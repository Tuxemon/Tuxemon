# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from tuxemon.db import EvolutionType, StatType
from tuxemon.event import MapCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.monster import Monster
from tuxemon.session import Session
from tuxemon.tools import compare


class CheckEvolutionCondition(EventCondition):
    """
    Check to see the player has at least one tuxemon evolving.
    If yes, it'll save the monster and the evolution inside a list.
    The list will be used by the event action "evolution".

    Script usage:
        .. code-block::

            is check_evolution <method>

    Script parameters:
        method: Method or methods of evolution.
        "all" means all the existing methods.

    eg. "is check_evolution standard"
    eg. "is check_evolution standard"
    ef. "is check_evolution standard:tech:stat"
    ef. "is check_evolution all"

    Note: methods of evolution are element, gender, location,
        variable, standard, stat, traded and tech.

    """

    name = "check_evolution"

    def test(self, session: Session, condition: MapCondition) -> bool:
        player = session.player
        client = session.client
        _evolution: bool = False

        self.method = condition.parameters[0]

        methods: list[str] = []
        evolution_type: list[EvolutionType] = []
        # recognize if single or multiple
        if self.method == "all":
            evolution_type = list(EvolutionType)
        else:
            methods = self.method.split(":")

        # keep evolution type and remove not valid (+ debug)
        if methods:
            for method in methods:
                if method in list(EvolutionType):
                    method = EvolutionType(method)
                    evolution_type.append(method)
                else:
                    raise ValueError(
                        f"{method} isn't among {list(EvolutionType)}"
                    )

        evolving: list[tuple[Monster, Monster]] = []
        for monster in player.monsters:
            if monster.evolutions:
                evolved = Monster()
                for evolution in monster.evolutions:
                    evolved.load_from_db(evolution.monster_slug)
                    if evolution.at_level <= monster.level:
                        for _method in evolution_type:
                            if _method == EvolutionType.standard:
                                evolving.append((monster, evolved))
                                _evolution = True
                            elif (
                                _method == EvolutionType.gender
                                and evolution.gender == monster.gender
                            ):
                                evolving.append((monster, evolved))
                                _evolution = True
                            elif (
                                _method == EvolutionType.element
                                and player.has_type(evolution.element)
                            ):
                                evolving.append((monster, evolved))
                                _evolution = True
                            elif (
                                _method == EvolutionType.tech
                                and player.has_tech(evolution.tech)
                            ):
                                evolving.append((monster, evolved))
                                _evolution = True
                            elif (
                                _method == EvolutionType.location
                                and evolution.inside == client.map_inside
                            ):
                                evolving.append((monster, evolved))
                                _evolution = True
                            elif (
                                _method == EvolutionType.traded
                                and evolution.traded == monster.traded
                            ):
                                evolving.append((monster, evolved))
                                _evolution = True
                            elif (
                                _method == EvolutionType.stat
                                and evolution.stats
                            ):
                                params = evolution.stats.split(":")
                                operator = params[1]
                                stat1 = monster.return_stat(
                                    StatType(params[0])
                                )
                                stat2 = monster.return_stat(
                                    StatType(params[2])
                                )
                                evolving.append((monster, evolved))
                                _evolution = compare(operator, stat1, stat2)
                            elif (
                                _method == EvolutionType.variable
                                and evolution.variable
                            ):
                                parts = evolution.variable.split(":")
                                key = parts[0]
                                value = parts[1]
                                if (
                                    key in player.game_variables
                                    and player.game_variables[key] == value
                                ):
                                    evolving.append((monster, evolved))
                                    _evolution = True
        if evolving:
            player.pending_evolutions = evolving
        return _evolution
