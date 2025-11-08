# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, final

from tuxemon.event.eventaction import EventAction

if TYPE_CHECKING:
    from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class QuitWorldAction(EventAction):
    """
    Exit the current world without quitting the game.

    Script usage:
        .. code-block::

            quit_world
    """

    name = "quit_world"

    def start(self, session: Session) -> None:
        session.client.camera_manager.reset()
        session.client.npc_manager.clear_npcs()
        session.client.current_music.stop()
        session.client.event_engine.reset()
        session.client.map_manager.clear_events()
        session.client.map_manager.clear_inits()
        session.client.replace_state("StartState")
        session.reset(reset_client=False)
        session.reset_time()
