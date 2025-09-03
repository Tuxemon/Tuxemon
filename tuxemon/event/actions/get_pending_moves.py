# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event.eventaction import EventAction
from tuxemon.menu.interface import MenuItem
from tuxemon.monster import Monster
from tuxemon.session import Session
from tuxemon.states.techniques import TechniqueMenuState
from tuxemon.technique.technique import Technique

logger = logging.getLogger(__name__)


@final
@dataclass
class GetPendingMovesAction(EventAction):
    """
    Display a menu of pending techniques for monsters listed in
    event_data["check_max_tech"], and store the selected technique ID
    in a game variable.

    Script usage:
        .. code-block::

            get_pending_moves <variable_name>

    Script parameters:
        variable_name: Name of the game variable to store the selected
            technique ID.

    Example:
        - "get_pending_moves chosen_move"
    """

    name = "get_pending_moves"
    variable_name: str

    def validate(self, technique: Optional[Technique]) -> bool:
        monster = self.monster

        if technique is None:
            return False

        if not monster.moves.can_forget(technique):
            logger.debug(
                f"Technique '{technique.slug}' is not forgettable — skipping."
            )
            return False

        logger.debug(f"Technique '{technique.slug}' is valid for selection.")
        return True

    def set_var(self, menu_item: MenuItem[Technique]) -> None:
        technique = menu_item.game_object

        self.session.player.game_variables[self.variable_name] = (
            technique.instance_id.hex
        )
        self.session.client.pop_state()

    def start(self, session: Session) -> None:
        self.session = session
        player = session.player

        monsters: list[Monster] = session.client.event_data.get(
            "check_max_tech", []
        )
        if not monsters:
            logger.warning("No monsters found in event_data['check_max_tech']")
            return

        for mon in monsters:
            self.monster = mon
            menu = session.client.push_state(
                TechniqueMenuState(
                    character=player,
                    techniques=mon.moves.get_moves(),
                    monster=mon,
                )
            )
            menu.escape_key_exits = False
            menu.is_valid_entry = self.validate  # type: ignore[method-assign]
            menu.on_menu_selection = self.set_var  # type: ignore[assignment]

        session.client.event_data.pop("check_max_tech", None)

    def update(self, session: Session) -> None:
        try:
            session.client.get_state_by_name("TechniqueMenuState")
        except ValueError:
            self.stop()
