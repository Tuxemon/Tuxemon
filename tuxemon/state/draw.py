# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

import pygame
from pygame.font import Font, get_default_font
from pygame.surface import Surface

from tuxemon.graphics import ColorLike
from tuxemon.platform.const.graphics import GREEN_COLOR, RED_COLOR
from tuxemon.ui.text_renderer import TextRenderer

if TYPE_CHECKING:
    from tuxemon.config import TuxemonConfig
    from tuxemon.db import SpatialCondition
    from tuxemon.prepare import DisplayContext
    from tuxemon.state.manager import StateManager
    from tuxemon.state.state import State


class Renderer:
    def __init__(
        self,
        screen: Surface,
        state_drawer: StateDrawer,
        config: TuxemonConfig,
        debug_drawer: EventDebugDrawer,
    ) -> None:
        """
        Initializes the Renderer class.

        The Renderer handles all drawing and rendering-related operations,
        including state rendering, optional debug overlays, and saving frames
        to disk.

        Parameters:
            screen: The pygame screen surface where everything is drawn.
            state_drawer: Handles rendering the current game state.
            config: Configuration settings that may affect rendering
                behavior.
            debug_drawer: Component used to render debug overlays, such as
                event conditions and collision maps.
        """
        self.screen = screen
        self.state_drawer = state_drawer
        self.debug_drawer = debug_drawer
        self.caption = config.window_caption
        self.vsync = config.vsync
        self.frames = 0
        self.fps_timer = 0.0

    def draw(self) -> None:
        """Draws the current game state."""
        self.state_drawer.draw()

    def draw_debug(
        self, partial_events: list[Sequence[tuple[bool, SpatialCondition]]]
    ) -> None:
        """Draws debug overlays if enabled."""
        self.debug_drawer.draw_event_debug(partial_events)

    def save_frame(self, frame_number: int) -> None:
        """Saves the current frame to disk."""
        filename = f"snapshot{frame_number:05d}.tga"
        pygame.image.save(self.screen, filename)

    def update(self, clock_tick: float) -> None:
        """
        Updates and displays the frames per second (FPS) on the window caption.

        This function calculates FPS based on elapsed time and updates the
        window caption to reflect the current FPS.

        Parameters:
            clock_tick: The time elapsed (in seconds) since the last update.
        """
        self.fps_timer += clock_tick
        self.frames += 1
        if self.fps_timer >= 1.0:
            fps = self.frames / self.fps_timer
            vsync_status = "VSync ON" if self.vsync else "VSync OFF"
            with_fps = f"{self.caption} - {fps:.2f} FPS - {vsync_status}"
            pygame.display.set_caption(with_fps)
            self.fps_timer = 0.0
            self.frames = 0


class StateDrawer:
    def __init__(
        self,
        surface: Surface,
        state_manager: StateManager,
        config: TuxemonConfig,
    ) -> None:
        """
        Initializes the StateDrawer.

        Responsible for managing the drawing of active states onto the
        given surface. This class iterates through the layers of active
        states, ensuring optimal rendering strategies based on transparency
        and layering requirements.

        Parameters:
            surface: The target surface where states will be drawn.
            state_manager: Manages the list of active states to be drawn.
            config: Configuration settings that may affect rendering
                behavior.
        """
        self.surface = surface
        self.state_manager = state_manager
        self.config = config

    def draw(self) -> None:
        """Draw all active states to the surface."""
        to_draw: list[State] = []
        full_screen = self.surface.get_rect()

        # Collect states to be drawn.
        for state in self.state_manager.active_states:
            to_draw.append(state)

            if (
                not state.transparent
                and state.rect == full_screen
                and not state.force_draw
            ):
                break

        # Draw states from bottom to top for proper layering.
        for state in reversed(to_draw):
            state.draw(self.surface)


class EventDebugDrawer:
    def __init__(
        self,
        context: DisplayContext,
        max_width: int = 1000,
        x_offset: int = 20,
        y_offset: int = 200,
        initial_x: int = 4,
        initial_y: int = 20,
        success_color: ColorLike = GREEN_COLOR,
        failure_color: ColorLike = RED_COLOR,
    ) -> None:
        """
        Initializes the EventDebugDrawer.

        Handles the drawing of event debug overlays on the provided screen.
        This class is responsible for rendering event-related data for
        debugging purposes using customizable font size, colors, and
        positioning.

        Parameters:
            screen: The screen surface where the debug overlay will be drawn.
            max_width: Maximum width allowed for rendering the overlay before
                wrapping.
            x_offset: Horizontal spacing between event sections.
            y_offset: Vertical spacing between event lines.
            initial_x: The starting x-coordinate for rendering the overlay.
            initial_y: The starting y-coordinate for rendering the overlay.
            valid_color: Color used to indicate valid conditions.
            invalid_color: Color used to indicate invalid conditions.
        """
        self.screen = context.screen
        self.scaling = context.scaling
        self.max_width = max_width
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.initial_x = initial_x
        self.initial_y = initial_y
        self.success_color = success_color
        self.failure_color = failure_color

    def draw_event_debug(
        self, partial_events: list[Sequence[tuple[bool, SpatialCondition]]]
    ) -> None:
        """Overlay event data on the screen."""
        initial_x, initial_y = self.initial_x, self.initial_y
        current_x, current_y = initial_x, initial_y

        for event in partial_events:
            max_width = 0
            for valid, item in event:
                parameters = " ".join(item.parameters)
                text = f"{item.operator} {item.type}: {parameters}"
                color = self.success_color if valid else self.failure_color
                size = self.render_text(text, color, (current_x, current_y))

                current_y += size[1]
                max_width = max(max_width, size[0])

            current_x += max_width + self.x_offset

            if current_x > self.max_width:
                current_x = initial_x
                initial_y += self.y_offset

            current_y = initial_y

    def render_text(
        self,
        text: str,
        color: ColorLike,
        position: tuple[int, int],
        font_size: int = 15,
    ) -> tuple[int, int]:
        font = Font(get_default_font(), font_size)
        renderer = TextRenderer(
            scaling=self.scaling, font=font, font_color=color
        )
        image = renderer.shadow_text(text)
        self.screen.blit(image, position)
        return image.get_size()
