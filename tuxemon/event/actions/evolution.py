# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import partial
from typing import final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.locale import T
from tuxemon.monster import Monster
from tuxemon.tools import open_choice_dialog, open_dialog

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

    """

    name = "evolution"
    npc_slug: str

    def start(self) -> None:
        client = self.session.client
        character = get_npc(self.session, self.npc_slug)
        if character is None:
            logger.error(f"{self.npc_slug} not found")
            return
        # this function cleans up the previous state without crashing
        if len(client.state_manager.active_states) > 2:
            return

        def positive_answer(monster: Monster, evolved: Monster) -> None:
            client.pop_state()
            client.pop_state()
            logger.info(f"{monster.name} evolves into {evolved.name}!")
            character.evolve_monster(monster, evolved.slug)

        def negative_answer() -> None:
            monster.got_experience = False
            monster.levelling_up = False
            logger.info(f"{monster.name}'s evolution refused!")
            client.pop_state()
            client.pop_state()

        def question_evolution(monster: Monster, evolved: Monster) -> None:
            params = {
                "name": monster.name.upper(),
                "evolve": evolved.name.upper(),
            }
            msg = T.format("evolution_confirmation", params)
            open_dialog(self.session, [msg])
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

        if character.pending_evolutions:
            evolutions = set(character.pending_evolutions)
            character.pending_evolutions.clear()
            for _monster in evolutions:
                monster = _monster[0]
                evolved = _monster[1]
                if monster.got_experience and monster.levelling_up:
                    question_evolution(monster, evolved)
