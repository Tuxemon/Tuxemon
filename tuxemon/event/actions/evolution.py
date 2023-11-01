# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from functools import partial
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.locale import T
from tuxemon.monster import Monster
from tuxemon.tools import open_choice_dialog, open_dialog


@final
@dataclass
class EvolutionAction(EventAction):
    """
    Checks, asks and evolves.

    Script usage:
        .. code-block::

            evolution

    """

    name = "evolution"

    def start(self) -> None:
        player = self.session.player
        client = self.session.client
        # this function cleans up the previous state without crashing
        if len(client.state_manager.active_states) > 2:
            return

        def positive_answer(monster: Monster, evolved: Monster) -> None:
            client.pop_state()
            client.pop_state()
            player.evolve_monster(monster, evolved.slug)

        def negative_answer() -> None:
            monster.got_experience = False
            monster.levelling_up = False
            client.pop_state()
            client.pop_state()

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

        if player.pending_evolutions:
            evolutions = set(player.pending_evolutions)
            player.pending_evolutions.clear()
            for _monster in evolutions:
                monster = _monster[0]
                evolved = _monster[1]
                if monster.got_experience and monster.levelling_up:
                    question_evolution(monster, evolved)
