# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import time

from tuxemon.base_client import BaseClient, ClientState
from tuxemon.config import TuxemonConfig

logger = logging.getLogger(__name__)


class HeadlessClient(BaseClient):
    """
    Headless client for server-side processing of game logic.
    This client runs without graphics, only handling events and
    game state updates.

    Parameters:
        config: The configuration for the game.
    """

    def __init__(self, config: TuxemonConfig) -> None:
        super().__init__(config)

    def main(self) -> None:
        """
        Initiates the main game loop.

        Since we are using Asteria networking to handle network events,
        we pass this session.Client instance to networking which in turn
        executes the "main_loop" method every frame.
        This leaves the networking component responsible for the main loop.
        """
        update = self.update
        clock = time.time
        time_since_draw = 0.0
        last_update = clock()

        while self.state != ClientState.DONE:
            if self.state == ClientState.RUNNING:
                clock_tick = clock() - last_update
                last_update = clock()
                time_since_draw += clock_tick
                update(clock_tick)
                time.sleep(0.01)
            elif self.state == ClientState.EXITING:
                self.perform_cleanup()
                self.state = ClientState.DONE

    def update(self, time_delta: float) -> None:
        """
        Main loop for entire game.

        This method gets update every frame
        by Asteria Networking's "listen()" function. Every frame we get the
        amount of time that has passed each frame, check game conditions,
        and update the game state.

        Parameters:
            time_delta: Elapsed time since last frame.
        """
        # self.network_manager.update(time_delta)
        events = self.input_manager.process_events()
        self.input_manager.update(time_delta)
        self.key_events = list(self.event_manager.process_events(events))
        self.event_data = {}
        self.event_engine.update(time_delta)

        if self.event_data:
            logger.debug("Event Data:" + str(self.event_data))

        self.update_states(time_delta)
