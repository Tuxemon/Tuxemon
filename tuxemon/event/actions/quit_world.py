# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
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
        client = session.client

        client.current_music.stop()
        client.camera_manager.reset()

        client.npc_manager.clear_npcs()
        client.event_engine.reset()
        client.map_manager.clear_events()
        client.map_manager.clear_inits()
        client.map_manager.clear_map()
        client.map_loader.clear_cache()

        for state_name in client.active_state_names:
            client.remove_state_by_name(state_name)

        session.reset(reset_client=False)
        session.reset_time()

        client.push_state("BackgroundState")
        client.push_state("StartState")
