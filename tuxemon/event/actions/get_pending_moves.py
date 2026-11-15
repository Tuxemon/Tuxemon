# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.locale.locale import T
from tuxemon.monster.monster import Monster
from tuxemon.session import Session
from tuxemon.states.monster_moves import MonsterMovesState
from tuxemon.technique.technique import Technique
from tuxemon.tools import open_dialog

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

    def validate(self, technique: Technique | None) -> bool:
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

    def set_var(self, technique: Technique) -> None:

        self.session.player.game_variables.set(
            self.variable_name, technique.instance_id.hex
        )

        new_tech = self.new_technique
        if technique.instance_id == new_tech.instance_id:
            msg = T.format("tech_no_learn", {"tech": new_tech.name})
        else:
            msg = T.format("tech_replaced", {"old": technique.name, "new": new_tech.name})

        client = self.session.client
        open_dialog(client, [msg], on_complete=client.pop_state)

    def start(self, session: Session) -> None:
        self.session = session

        monsters: list[Monster] = session.client.event_data.get(
            "check_max_tech", []
        )
        if not monsters:
            logger.warning("No monsters found in event_data['check_max_tech']")
            self.stop()
            return

        for mon in monsters:
            self.monster = mon
            self.new_technique = mon.moves.get_moves()[-1]
            state = session.client.push_state(
                MonsterMovesState(
                    client=session.client,
                    monster=mon,
                    source="GetPendingMovesAction",
                    monsters=None,
                    on_selection=self.set_var,
                    is_valid_entry=self.validate,
                )
            )
            state.escape_key_exits = False

        session.client.event_data.pop("check_max_tech", None)

    def update(self, session: Session, dt: float) -> None:
        if "MonsterMovesState" not in session.client.active_state_names:
            self.stop()
