# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import partial
from typing import TYPE_CHECKING, final

from tuxemon.db import EvolutionStage
from tuxemon.event.eventaction import EventAction
from tuxemon.locale.locale import T
from tuxemon.menu.interface import MenuItem
from tuxemon.monster.monster import Monster
from tuxemon.monster.stats import BasicStats
from tuxemon.states.technique_menu import TechniqueMenuState
from tuxemon.technique.technique import Technique
from tuxemon.tools import get_valid_uuid, open_choice_dialog, open_dialog
from tuxemon.ui.menu_options import MenuOptions, create_choice_options

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
            The action to perform. Can be one of:

            - "technique": Learn any move the monster hasn't acquired from its base
              moveset, without restrictions based on level or evolution stage.
            - "monster": Devolve the monster. The action finishes once the
              devolution menu has closed.
            - "tp": Reset the monster's training points, either for a single
              stat or for all stats at once. The action finishes once the
              stat menu and the confirmation dialog have both closed.
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
            self.stop()
            return  # Exit early if no valid UUID

        monster = session.client.get_monster_by_iid(monster_id)
        if monster is None:
            logger.debug(f"Monster {monster_id} not found.")
            self.stop()
            return

        self.monster = monster

        if self.option not in ["monster", "technique", "tp"]:
            logger.error(
                f"{self.option} must be 'monster', 'technique' or 'tp'"
            )
            self.stop()
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
                self.stop()
                return

            session.client.push_state(
                TechniqueMenuState(
                    client=session.client,
                    character=session.player,
                    techniques=self.monster.moves.current_moves,
                    on_selection=self.get_tech,
                )
            )
        elif self.option == "monster":
            actions = {
                mon.slug: partial(self.devolve, mon.slug)
                for mon in monster.history
                if self.monster.slug in mon.evolves_into
                and (
                    (
                        self.monster.stage == EvolutionStage.STAGE1
                        and mon.stage == EvolutionStage.BASIC
                    )
                    or (
                        self.monster.stage == EvolutionStage.STAGE2
                        and mon.stage
                        in [EvolutionStage.STAGE1, EvolutionStage.BASIC]
                    )
                )
            }

            menu_options = create_choice_options(actions)
            for opt in menu_options:
                opt.display_text = T.translate(opt.key)

            open_choice_dialog(session.client, MenuOptions(menu_options))
        else:
            actions = {
                name: partial(self.reset_tps, name)
                for name in BasicStats.names()
            }
            actions["dojo_tp_all"] = partial(self.reset_tps, None)

            menu_options = create_choice_options(actions)
            for opt in menu_options:
                opt.display_text = T.translate(opt.key)

            open_choice_dialog(session.client, MenuOptions(menu_options))

    def update(self, session: Session, dt: float) -> None:
        active = session.client.active_state_names
        if self.option in ("monster", "tp"):
            # These menus are a ChoiceState, not a DialogState. Wait until
            # the menu (and the "tp" confirmation dialog) have closed, so
            # that later actions in the event (e.g. charging money) run
            # after the player has made their choice.
            if "ChoiceState" not in active and "DialogState" not in active:
                self.stop()
        elif "DialogState" not in active:
            self.stop()

    def devolve(self, slug: str) -> None:
        devolution = Monster.spawn_base(slug, self.monster.level)
        devolution.transfer_properties_from(self.monster)
        self.monster.evolution_handler.evolve_monster(devolution)
        logger.info(f"{self.monster.name}'s devolved!")
        self.client.sound_manager.play("sound_confirm")
        self.client.pop_state()

    def reset_tps(self, stat: str | None) -> None:
        if stat is None:
            stats = BasicStats.names()
            label = T.translate("dojo_tp_all_stats")
        else:
            stats = [stat]
            label = T.translate(stat)
        for name in stats:
            self.monster.training_points.set_stat(name, 0)
        self.monster.training_points.validate()
        self.monster.set_stats()
        logger.info(f"{self.monster.name}'s training points reset: {stats}")
        self.client.sound_manager.play("sound_confirm")
        self.client.pop_state()
        open_dialog(
            self.client,
            [T.format("dojo_tp_reset_done", {"stat": label})],
        )

    def set_var(self, menu_technique: MenuItem[Technique]) -> None:
        tech = menu_technique.game_object
        self.monster.moves.learn(self.monster, tech, ignore_eligibility=True)
        logger.info(f"{tech.name} learned!")
        self.client.sound_manager.play("sound_confirm")
        self.client.pop_state()

    def get_tech(self, menu_technique: MenuItem[Technique]) -> None:
        tech = menu_technique.game_object
        self.monster.moves.remove_forced(tech)
        logger.info(f"{tech.name} forgot!")
        self.client.sound_manager.play("sound_confirm")
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
            self.stop()
            return

        if len(learnable_moves) == 1:
            tech = learnable_moves[0]
            self.monster.moves.learn(
                self.monster, tech, ignore_eligibility=True
            )
            logger.info(f"{tech.name} learned!")
            self.client.sound_manager.play("sound_confirm")
            self.stop()
            return

        self.client.push_state(
            TechniqueMenuState(
                client=self.client,
                character=self.player,
                techniques=learnable_moves,
                on_selection=self.set_var,
            )
        )
