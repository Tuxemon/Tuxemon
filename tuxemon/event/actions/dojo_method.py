# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import partial
from typing import TYPE_CHECKING, final

from tuxemon.db import EvolutionStage
from tuxemon.event import get_monster_by_iid
from tuxemon.event.eventaction import EventAction
from tuxemon.locale import T
from tuxemon.menu.interface import MenuItem
from tuxemon.monster import Monster
from tuxemon.states.technique_menu import TechniqueMenuState
from tuxemon.technique.technique import Technique
from tuxemon.tools import get_valid_uuid, open_choice_dialog
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

        .. code-block:: text

           dojo_method <variable_name>,<option>

    Script Parameters:

        variable_name:
            The name of the variable where the monster ID will be stored.

        option:
            The action to perform. Can be either:

            - "technique": Learn any move the monster hasn't acquired from its base
              moveset, without restrictions based on level or evolution stage.
            - "monster": Devolve the monster.

    """

    name = "dojo_method"
    variable_name: str
    option: str

    def start(self, session: Session) -> None:
        self.client = session.client
        self.player = session.player

        monster_id = get_valid_uuid(
            self.player.game_variables, self.variable_name
        )
        if monster_id is None:
            logger.info(
                f"No valid monster selected for variable '{self.variable_name}'"
            )
            return  # Exit early if no valid UUID

        monster = get_monster_by_iid(session, monster_id)
        if monster is None:
            logger.debug(f"Monster {monster_id} not found.")
            return

        self.monster = monster

        if self.option not in ["monster", "technique"]:
            logger.error(f"{self.option} must be 'monster' or 'technique'")
            return

        if self.option == "technique":

            learnable_moves = [
                Technique.create(tech.technique)
                for tech in self.monster.moves.moveset
                if not self.monster.moves.has_move(tech.technique)
                and tech.level_learned <= self.monster.level
            ]

            if not learnable_moves:
                session.player.game_variables.set("dojo_notech", "on")
                return

            forget = session.client.push_state(
                TechniqueMenuState(
                    character=session.player,
                    techniques=self.monster.moves.current_moves,
                )
            )
            forget.on_menu_selection = self.get_tech  # type: ignore[method-assign]
        else:
            menu_options: list[ChoiceOption] = []
            devolvable_monsters = [
                mon
                for mon in monster.history
                if self.monster.slug in mon.evolves_into
                and (
                    (
                        self.monster.stage == EvolutionStage.stage1
                        and mon.stage == EvolutionStage.basic
                    )
                    or (
                        self.monster.stage == EvolutionStage.stage2
                        and mon.stage
                        in [EvolutionStage.stage1, EvolutionStage.basic]
                    )
                )
            ]

            for mon in devolvable_monsters:
                menu_options.append(
                    ChoiceOption(
                        key=mon.slug,
                        display_text=T.translate(mon.slug),
                        action=partial(self.devolve, mon.slug),
                    )
                )

            open_choice_dialog(session.client, MenuOptions(menu_options))

    def update(self, session: Session, dt: float) -> None:
        try:
            session.client.get_state_by_name("DialogState")
        except ValueError:
            self.stop()

    def devolve(self, slug: str) -> None:
        devolution = Monster.create(slug)
        self.monster.evolution_handler.evolve_monster(devolution)
        logger.info(f"{self.monster.name}'s devolved!")
        self.client.sound_manager.play_sound("sound_confirm")
        self.client.pop_state()

    def set_var(self, menu_technique: MenuItem[Technique]) -> None:
        tech = menu_technique.game_object
        self.monster.moves.learn(self.monster, tech, ignore_eligibility=True)
        logger.info(f"{tech.name} learned!")
        self.client.sound_manager.play_sound("sound_confirm")
        self.client.pop_state()

    def get_tech(self, menu_technique: MenuItem[Technique]) -> None:
        tech = menu_technique.game_object
        self.monster.moves.remove_forced(tech)
        logger.info(f"{tech.name} forgot!")
        self.client.sound_manager.play_sound("sound_confirm")
        self.client.pop_state()

        # Now push the learn menu
        learnable_moves = [
            Technique.create(tech.technique)
            for tech in self.monster.moves.moveset
            if not self.monster.moves.has_move(tech.technique)
            and tech.level_learned <= self.monster.level
        ]
        if not learnable_moves:
            self.player.game_variables.set("dojo_notech", "on")
            return

        if len(learnable_moves) == 1:
            tech = learnable_moves[0]
            self.monster.moves.learn(
                self.monster, tech, ignore_eligibility=True
            )
            logger.info(f"{tech.name} learned!")
            self.client.sound_manager.play_sound("sound_confirm")
            return

        relearn = self.client.push_state(
            TechniqueMenuState(
                character=self.player,
                techniques=learnable_moves,
            )
        )
        relearn.on_menu_selection = self.set_var  # type: ignore[method-assign]
