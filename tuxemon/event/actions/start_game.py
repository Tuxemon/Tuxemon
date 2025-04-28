# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon import prepare
from tuxemon.event.eventaction import EventAction
from tuxemon.time_handler import today_ordinal

logger = logging.getLogger(__name__)


@final
@dataclass
class StartGameAction(EventAction):
    """
    Starts a new game session and initializes gameplay components.

    Script usage:
        .. code-block::

            start_game <map_name>,<mod>

    Script parameters:
        map_name: The name of the starting map.
        mod: The name of the mod.
    """

    name = "start_game"
    map_name: str
    mod: str

    def start(self) -> None:
        map_path = prepare.fetch("maps", f"{self.map_name}{self.mod}.tmx")
        logger.info(
            f"Starting game with map: {self.map_name} and mod: {self.mod}"
        )
        logger.info(f"Map path resolved to: {map_path}")
        self.session.client.push_state("WorldState", map_name=map_path)
        game_var = self.session.player.game_variables
        game_var["date_start_game"] = today_ordinal()
