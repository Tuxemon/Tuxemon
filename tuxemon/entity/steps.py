# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from tuxemon.event import get_event_bus
from tuxemon.monster.listener import monster_update_listener

if TYPE_CHECKING:
    from tuxemon.entity.entity import Entity
    from tuxemon.entity.npc import NPC
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session
    from tuxemon.step_tracker import StepTrackerManager

logger = logging.getLogger(__name__)

get_event_bus().subscribe(
    "player_steps_moved", monster_update_listener, priority=5
)


class StepManager:
    """
    Handles all game logic related to character movement steps.

    This includes updating individual monster step counts, ticking
    step-based status effects (like Poison), and updating general
    game StepTrackerManagers.
    """

    def __init__(
        self,
        session: Session,
        step_tracker_manager: StepTrackerManager,
        owner: NPC,
    ) -> None:
        self.session = session
        self.step_tracker = step_tracker_manager
        self.owner = owner
        session.client.event_bus.subscribe(
            "entity_moved",
            self._on_entity_moved,
            priority=10,
        )

    def handle_steps(
        self,
        diff_x: float,
        diff_y: float,
        steps_moved: float,
        monsters_in_party: list[Monster],
    ) -> None:
        """
        Publishes a 'player_steps_moved' event with movement details.

        Parameters:
            steps_moved: Distance moved since the last frame.
            monsters_in_party: Monsters currently in the player's party.
        """
        if steps_moved == 0:
            return
        self.step_tracker.update_all(diff_x=diff_x, diff_y=diff_y)
        self.session.client.event_bus.publish(
            "player_steps_moved",
            diff_x=diff_x,
            diff_y=diff_y,
            steps=steps_moved,
            monsters=monsters_in_party,
            session=self.session,
        )

    def _on_entity_moved(
        self,
        entity: Entity,
        diff_x: float,
        diff_y: float,
        steps: float,
        **kwargs: Any,
    ) -> None:
        if entity is not self.owner:
            return

        entity.steps += steps
        entity.daycare.on_steps(steps)

        self.handle_steps(
            diff_x=diff_x,
            diff_y=diff_y,
            steps_moved=steps,
            monsters_in_party=entity.monsters,
        )
