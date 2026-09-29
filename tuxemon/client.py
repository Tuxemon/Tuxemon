# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import TYPE_CHECKING

import pygame

from tuxemon.base_client import BaseClient, ClientState
from tuxemon.config import TuxemonConfig
from tuxemon.map.tuxemon import NullMap
from tuxemon.map.view import DebugRenderer, MapRenderer, NullRenderer
from tuxemon.state.draw import EventDebugDrawer, Renderer, StateDrawer

if TYPE_CHECKING:
    from tuxemon.prepare import DisplayContext

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
        cls, config: TuxemonConfig, context: DisplayContext
    ) -> LocalPygameClient:
        """
        Initialize the LocalPygameClient with the given configuration and screen.
        """
        try:
            client = LocalPygameClient(config, context)
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

    def __init__(self, config: TuxemonConfig, context: DisplayContext):
        super().__init__(config, context)

        # movie creation
        self.frame_number = 0
        self.save_to_disk = False

        # Initialize drawers
        self.state_drawer = StateDrawer(
            self.screen, self.state_manager, config
        )
        self.event_debug_drawer = EventDebugDrawer(self.context)
        self.renderer = Renderer(
            self.screen,
            self.state_drawer,
            self.config,
            self.event_debug_drawer,
        )
        self.debug_renderer = DebugRenderer(
            self.map_manager, self.npc_manager, self.context
        )
        map_renderer = MapRenderer(
            self.camera_manager,
            self.npc_manager,
            self.debug_renderer,
            self.context,
        )
        self.set_renderer(map_renderer)

    def reset_renderer(self) -> None:
        current_map = self.map_manager.current_map
        if isinstance(current_map, NullMap):
            self.set_renderer(NullRenderer())
            logger.debug("Renderer reset to NullRenderer.")
        else:
            self.debug_renderer = DebugRenderer(
                self.map_manager, self.npc_manager, self.context
            )
            map_renderer = MapRenderer(
                self.camera_manager,
                self.npc_manager,
                self.debug_renderer,
                self.context,
            )
            self.set_renderer(map_renderer)
            logger.debug("Renderer reset to MapRenderer.")

    def main(self) -> None:
        """
        Initiates the main game loop with a fixed timestep.
        """
        update = self.update
        draw = self.draw
        screen = self.screen
        flip = pygame.display.update
        clock = time.time

        target_fps = self.config.fps
        frame_length = 1.0 / target_fps

        last_time = clock()
        accumulator = 0.0

        while self.state != ClientState.DONE:
            if self.state == ClientState.RUNNING:
                now = clock()
                dt = now - last_time
                last_time = now

                # Prevent spiral of death if the game lags
                if dt > 0.25:
                    dt = 0.25

                accumulator += dt

                while accumulator >= frame_length:
                    update(frame_length)
                    accumulator -= frame_length

                draw()
                self.input_manager.draw_inputs(screen)
                flip()

                if self.config.show_fps:
                    self.renderer.update(frame_length)

            elif self.state == ClientState.EXITING:
                self.perform_cleanup()
                self.state = ClientState.DONE

    def update(self, dt: float) -> None:
        """Main loop for entire game."""
        self.update_states(dt)

    def queue_command(self, command: Callable[[], None]) -> None:
        self.command_queue.put(command)
        logger.debug("Queued command for execution in main thread.")

    def draw(self) -> None:
        """Centralized draw logic."""
        self.renderer.draw()

        if self.config.collision_map:
            self.renderer.draw_debug(self.event_engine.partial_events)

        if self.save_to_disk:
            self.renderer.save_frame(self.frame_number)

        self.frame_number += 1
