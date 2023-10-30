# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from functools import partial
from typing import final

from tuxemon.db import EvolutionType
from tuxemon.event.eventaction import EventAction
from tuxemon.locale import T
from tuxemon.monster import Monster
from tuxemon.tools import open_choice_dialog, open_dialog


@final
@dataclass
class EvolutionAction(EventAction):
    """
    Checks, asks and evolves.

    """

    name = "evolution"

    def start(self) -> None:
        # this function cleans up the previous state without crashing
        if len(self.session.client.state_manager.active_states) > 2:
            self.session.client.pop_state()

        player = self.session.player

        def positive_answer(monster: Monster, evolved: Monster) -> None:
            self.session.client.pop_state()
            self.session.client.pop_state()
            self.session.player.evolve_monster(monster, evolved.slug)

        def negative_answer() -> None:
            self.session.client.pop_state()
            self.session.client.pop_state()

        def question_evolution(monster: Monster, evolved: Monster) -> None:
            open_dialog(
                self.session,
                [
                    T.format(
                        "evolution_confirmation",
                        {
                            "name": monster.name.upper(),
                            "evolve": evolved.name.upper(),
                        },
                    )
                ],
            )
            open_choice_dialog(
                self.session,
                menu=(
                    (
                        "yes",
                        T.translate("yes"),
                        partial(
                            positive_answer,
                            monster,
                            evolved,
                        ),
                    ),
                    (
                        "no",
                        T.translate("no"),
                        negative_answer,
                    ),
                ),
            )

        for monster in player.monsters:
            for evolution in monster.evolutions:
                evolved = Monster()
                evolved.load_from_db(evolution.monster_slug)
                if evolution.path == EvolutionType.standard:
                    if evolution.at_level <= monster.level:
                        question_evolution(monster, evolved)
                elif evolution.path == EvolutionType.gender:
                    if evolution.at_level <= monster.level:
                        if evolution.gender == monster.gender:
                            question_evolution(monster, evolved)
                elif evolution.path == EvolutionType.element:
                    if evolution.at_level <= monster.level:
                        if player.has_type(evolution.element):
                            question_evolution(monster, evolved)
                elif evolution.path == EvolutionType.tech:
                    if evolution.at_level <= monster.level:
                        if player.has_tech(evolution.tech):
                            question_evolution(monster, evolved)
                elif evolution.path == EvolutionType.location:
                    if evolution.at_level <= monster.level:
                        if evolution.inside == self.session.client.map_inside:
                            question_evolution(monster, evolved)
                elif evolution.path == EvolutionType.stat:
                    if evolution.at_level <= monster.level:
                        if monster.return_stat(
                            evolution.stat1
                        ) >= monster.return_stat(evolution.stat2):
                            question_evolution(monster, evolved)
                elif evolution.path == EvolutionType.season:
                    if evolution.at_level <= monster.level:
                        if evolution.season == player.game_variables["season"]:
                            question_evolution(monster, evolved)
                elif evolution.path == EvolutionType.daytime:
                    if evolution.at_level <= monster.level:
                        if (
                            evolution.daytime
                            == player.game_variables["daytime"]
                        ):
                            question_evolution(monster, evolved)
