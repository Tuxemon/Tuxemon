# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from tuxemon.db import EvolutionType
from tuxemon.event import MapCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.monster import Monster
from tuxemon.session import Session


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

    Note: methods of evolution are element, gender,
        location, variable, standard, stat and tech.

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
        if self.method.find(":") > 1:
            methods = self.method.split(":")
        else:
            if self.method == "all":
                evolution_type = list(EvolutionType)
            else:
                methods.append(self.method)

        # keep evolution type and remove not valid (+ debug)
        if methods:
            for method in methods:
                if method in list(EvolutionType):
                    method = EvolutionType(method)
                    evolution_type.append(method)
                else:
                    raise ValueError(
                        f"{method} isn't a valid method of evolution"
                    )

        evolving: list[tuple[Monster, Monster]] = []
        for monster in player.monsters:
            if monster.evolutions:
                evolved = Monster()
                for evolution in monster.evolutions:
                    evolved.load_from_db(evolution.monster_slug)
                    for _method in evolution_type:
                        if evolution.path == _method:
                            if evolution.at_level <= monster.level:
                                evolving.append((monster, evolved))
                                _evolution = True
                        elif evolution.path == _method:
                            if evolution.at_level <= monster.level:
                                if evolution.gender == monster.gender:
                                    evolving.append((monster, evolved))
                                    _evolution = True
                        elif evolution.path == _method:
                            if evolution.at_level <= monster.level:
                                if player.has_type(evolution.element):
                                    evolving.append((monster, evolved))
                                    _evolution = True
                        elif evolution.path == _method:
                            if evolution.at_level <= monster.level:
                                if player.has_tech(evolution.tech):
                                    evolving.append((monster, evolved))
                                    _evolution = True
                        elif evolution.path == _method:
                            if evolution.at_level <= monster.level:
                                if evolution.inside == client.map_inside:
                                    evolving.append((monster, evolved))
                                    _evolution = True
                        elif evolution.path == _method:
                            if evolution.at_level <= monster.level:
                                if monster.return_stat(
                                    evolution.stat1
                                ) >= monster.return_stat(evolution.stat2):
                                    evolving.append((monster, evolved))
                                    _evolution = True
                        elif evolution.path == _method:
                            if (
                                evolution.at_level <= monster.level
                                and evolution.variable
                            ):
                                parts = evolution.variable.split(":")
                                key = parts[0]
                                value = parts[1]
                                exists = key in player.game_variables
                                if (
                                    exists
                                    and player.game_variables[key] == value
                                ):
                                    evolving.append((monster, evolved))
                                    _evolution = True
        if evolving:
            player.pending_evolutions = evolving
        return _evolution
