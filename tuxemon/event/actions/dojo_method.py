# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import partial
from typing import TYPE_CHECKING, final
from uuid import UUID

from tuxemon.event import get_monster_by_iid
from tuxemon.event.eventaction import EventAction
from tuxemon.locale import T
from tuxemon.monster import Monster
from tuxemon.technique.technique import Technique
from tuxemon.tools import open_choice_dialog
from tuxemon.ui.menu_options import ChoiceOption, MenuOptions

if TYPE_CHECKING:
    from tuxemon.session import Session

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
            - "technique": Learn any move the monster hasn't acquired from its base
                moveset, without restrictions based on level or evolution stage.
            - "monster": Devolve the monster.
    """

    name = "dojo_method"
    variable_name: str
    option: str

    def start(self, session: Session) -> None:
        self.client = session.client
        player = session.player
        monster_id = UUID(player.game_variables[self.variable_name])

        monster = get_monster_by_iid(session, monster_id)
        if monster is None:
            logger.debug(f"Monster {monster_id} not found.")
            return

        if self.option not in ["monster", "technique"]:
            logger.error(f"{self.option} must be 'monster' or 'technique'")
            return

        menu_options: list[ChoiceOption] = []

        if self.option == "technique":
            learnable_moves = [
                tech.technique
                for tech in monster.moves.moveset
                if not monster.moves.has_move(tech.technique)
            ]

            if not learnable_moves:
                session.player.game_variables["dojo_notech"] = "on"
                return

            if len(learnable_moves) == 1:
                logger.info(
                    f"{monster.name} automatically learned {learnable_moves[0]} via dojo (only option)"
                )
                self.learn(monster, learnable_moves[0])
                return

            for move in learnable_moves:
                menu_options.append(
                    ChoiceOption(
                        key=move,
                        display_text=T.translate(move),
                        action=partial(self.learn, monster, move),
                    )
                )

        else:
            devolvable_monsters = [
                mon
                for mon in monster.history
                if (monster.stage == "stage1" and mon.evo_stage == "basic")
                or (
                    monster.stage == "stage2"
                    and mon.evo_stage in ["stage1", "basic"]
                )
            ]

            for mon in devolvable_monsters:
                menu_options.append(
                    ChoiceOption(
                        key=mon.mon_slug,
                        display_text=T.translate(mon.mon_slug),
                        action=partial(self.devolve, monster, mon.mon_slug),
                    )
                )

        open_choice_dialog(session.client, MenuOptions(menu_options))

    def update(self, session: Session) -> None:
        try:
            session.client.get_state_by_name("DialogState")
        except ValueError:
            self.stop()

    def devolve(self, monster: Monster, slug: str) -> None:
        devolution = Monster.create(slug)
        monster.evolution_handler.evolve_monster(devolution)
        logger.info(f"{monster.name}'s devolved!")
        self.client.sound_manager.play_sound("sound_confirm")
        self.client.pop_state()

    def learn(self, monster: Monster, technique: str) -> None:
        tech = Technique.create(technique)
        monster.moves.learn(monster.instance_id, tech)
        logger.info(f"{tech.name} learned!")
        self.client.sound_manager.play_sound("sound_confirm")
        self.client.pop_state()
