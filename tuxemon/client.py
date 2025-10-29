# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import time
from threading import Thread

import pygame
from pygame.surface import Surface

from tuxemon.base_client import BaseClient, ClientState
from tuxemon.cli.processor import CommandProcessor
from tuxemon.config import TuxemonConfig
from tuxemon.map.map_view import DebugRenderer, MapRenderer
from tuxemon.session import local_session
from tuxemon.state.draw import EventDebugDrawer, Renderer, StateDrawer

logger = logging.getLogger(__name__)


class LocalPygameClient(BaseClient):
    """
    Client class for the entire project.

    Contains the game loop and the event_loop, which passes events to
    States as needed.

    Parameters:
        config: The configuration for the game.
        screen: The surface where the game is rendered.
    """

    @classmethod
    def create(
        cls, config: TuxemonConfig, screen: Surface
    ) -> LocalPygameClient:
        """
        Initialize the LocalPygameClient with the given configuration and screen.
        """
        try:
            client = LocalPygameClient(config, screen)
            logger.info("Client initialized successfully.")
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to initialize client: {e}")
            raise
        except Exception as e:
            logger.critical(
                f"Unexpected error during client initialization: {e}"
            )
            raise
        return client

    def __init__(self, config: TuxemonConfig, screen: Surface) -> None:
        super().__init__(config)
        self.screen = screen

        # movie creation
        self.frame_number = 0
        self.save_to_disk = False

        # Initialize drawers
        self.state_drawer = StateDrawer(
            self.screen, self.state_manager, config
        )
        self.event_debug_drawer = EventDebugDrawer(self.screen)
        self.renderer = Renderer(
            self.screen,
            self.state_drawer,
            self.config,
            self.event_debug_drawer,
        )
        self.debug_renderer = DebugRenderer(self.map_manager, self.npc_manager)
        map_renderer = MapRenderer(
            self.camera_manager, self.npc_manager, self.debug_renderer
        )
        self.set_renderer(map_renderer)

        if self.config.cli:
            local_session.set_client(self)
            self.cli = CommandProcessor(local_session)
            thread = Thread(target=self.cli.run)
            thread.daemon = True
            thread.start()

    def main(self) -> None:
        """
        Initiates the main game loop.

        Since we are using Asteria networking to handle network events,
        we pass this session.Client instance to networking which in turn
        executes the "main_loop" method every frame.
        This leaves the networking component responsible for the main loop.
        """
        update = self.update
        draw = self.draw
        screen = self.screen
        flip = pygame.display.update
        clock = time.time
        frame_length = 1.0 / self.config.fps
        time_since_draw = 0.0
        last_update = clock()

        while self.state != ClientState.DONE:
            if self.state == ClientState.RUNNING:
                clock_tick = clock() - last_update
                last_update = clock()
                time_since_draw += clock_tick
                update(clock_tick)
                if time_since_draw >= frame_length:
                    time_since_draw -= frame_length
                    draw()
                    if self.input_manager.controller_overlay:
                        self.input_manager.controller_overlay.draw(screen)
                    if self.input_manager.show_visualizer:
                        self.input_manager.draw_visualizer(screen)
                    flip()
                if self.config.show_fps:
                    self.renderer.update(clock_tick)
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
        and draw the game to the screen.

        Parameters:
            time_delta: Elapsed time since last frame.
        """
        self.network_manager.update(time_delta)
        events = self.input_manager.process_events()
        self.key_events = list(self.event_manager.process_events(events))
        self.event_data = {}
        self.event_engine.update(time_delta)

        if self.event_data:
            logger.debug("Event Data:" + str(self.event_data))

        self.update_states(time_delta)

    def draw(self) -> None:
        """Centralized draw logic."""
        self.renderer.draw()

        if self.config.collision_map:
            self.renderer.draw_debug(self.event_engine.partial_events)

        if self.save_to_disk:
            self.renderer.save_frame(self.frame_number)

        self.frame_number += 1
