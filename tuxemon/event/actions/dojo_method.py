# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from functools import partial
from typing import final

from tuxemon.event import get_monster_by_iid
from tuxemon.event.eventaction import EventAction
from tuxemon.locale import T
from tuxemon.monster import Monster
from tuxemon.states.dialog import DialogState
from tuxemon.technique.technique import Technique
from tuxemon.tools import open_choice_dialog

logger = logging.getLogger(__name__)


@final
@dataclass
class DojoMethodAction(EventAction):
    """
    Represents an event action for the monks in the Dojo (Spyder).

    Script Usage:
        .. code-block::

            dojo_method <variable_name>,<option>

    Script Parameters:
        variable_name: The name of the variable where the monster ID will be stored.
        option: The action to perform. Can be either:
            - "technique": Learn a forgotten technique from the monster's moveset.
            - "monster": Devolve the monster.

    """

    name = "dojo_method"
    variable_name: str
    option: str

    def start(self) -> None:
        self.client = self.session.client
        player = self.session.player
        monster_id = uuid.UUID(player.game_variables[self.variable_name])

        monster = get_monster_by_iid(self.session, monster_id)
        if monster is None:
            logger.debug(f"Monster {monster_id} not found.")
            return

        if self.option not in ["monster", "technique"]:
            logger.error(f"{self.option} must be 'monster' or 'technique'")
            return

        menu: list[tuple[str, str, Callable[[], None]]] = []

        if self.option == "technique":
            # Get the moves that the monster can learn but hasn't yet
            learnable_moves = [
                tech.technique
                for tech in monster.moveset
                if tech.level_learned <= monster.level
                and tech.technique not in [mov.slug for mov in monster.moves]
            ]

            if not learnable_moves:
                self.session.player.game_variables["dojo_notech"] = "on"
                return

            # Create menu options for each learnable move
            for move in learnable_moves:
                menu.append(
                    (
                        move,
                        T.translate(move),
                        partial(self.learn, monster, move),
                    )
                )
        else:
            # Get the monsters that the current monster can devolve into
            devolvable_monsters = [
                mon
                for mon in monster.history
                if (monster.stage == "stage1" and mon.evo_stage == "basic")
                or (
                    monster.stage == "stage2"
                    and mon.evo_stage in ["stage1", "basic"]
                )
            ]

            # Create menu options for each devolvable monster
            for mon in devolvable_monsters:
                menu.append(
                    (
                        mon.mon_slug,
                        T.translate(mon.mon_slug),
                        partial(self.devolve, monster, mon.mon_slug),
                    )
                )

        open_choice_dialog(self.session, menu)

    def update(self) -> None:
        try:
            self.session.client.get_state_by_name(DialogState)
        except ValueError:
            self.stop()

    def devolve(self, monster: Monster, slug: str) -> None:
        """Deny the evolution"""
        devolution = Monster()
        devolution.load_from_db(slug)
        monster.evolution_handler.evolve_monster(devolution)
        logger.info(f"{monster.name}'s devolved!")
        self.client.sound_manager.play_sound("sound_confirm")
        self.client.pop_state()

    def learn(self, monster: Monster, technique: str) -> None:
        """Deny the evolution"""
        tech = Technique()
        tech.load(technique)
        monster.learn(tech)
        logger.info(f"{tech.name} learned!")
        self.client.sound_manager.play_sound("sound_confirm")
        self.client.pop_state()
