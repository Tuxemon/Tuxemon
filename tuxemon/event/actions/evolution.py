# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from functools import partial
from typing import final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.locale import T
from tuxemon.monster import Monster
from tuxemon.tools import open_choice_dialog, open_dialog

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

    """

    name = "evolution"
    npc_slug: str

    def start(self) -> None:
        client = self.session.client
        character = get_npc(self.session, self.npc_slug)
        if character is None:
            logger.error(f"{self.npc_slug} not found")
            return

        self.character = character
        self.client = self.session.client

        if len(client.state_manager.active_states) > MAX_ACTIVE_STATES:
            return

        self.process_pending_evolutions()

    def process_pending_evolutions(self) -> None:
        """Process pending evolutions for the character"""
        evolutions = set(self.character.pending_evolutions)
        self.character.pending_evolutions.clear()
        for monster, evolved in evolutions:
            if monster.got_experience and monster.levelling_up:
                self.question_evolution(monster, evolved)

    def question_evolution(self, monster: Monster, evolved: Monster) -> None:
        """Ask the user to confirm the evolution"""
        params = {
            "name": monster.name.upper(),
            "evolve": evolved.name.upper(),
        }
        msg = T.format("evolution_confirmation", params)
        open_dialog(self.session, [msg])
        _no = T.translate("no")
        _yes = T.translate("yes")
        menu: list[tuple[str, str, Callable[[], None]]] = []
        menu.append(
            ("yes", _yes, partial(self.confirm_evolution, monster, evolved))
        )
        menu.append(("no", _no, partial(self.deny_evolution, monster)))
        open_choice_dialog(self.session, menu)

    def confirm_evolution(self, monster: Monster, evolved: Monster) -> None:
        """Confirm the evolution"""
        self.client.pop_state()
        self.client.pop_state()
        logger.info(f"{monster.name} evolves into {evolved.name}!")
        self.character.evolve_monster(monster, evolved.slug)

    def deny_evolution(self, monster: Monster) -> None:
        """Deny the evolution"""
        monster.got_experience = False
        monster.levelling_up = False
        logger.info(f"{monster.name}'s evolution refused!")
        self.client.pop_state()
        self.client.pop_state()
