# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from pygame import draw
from pygame.font import Font
from pygame.rect import Rect
from pygame.surface import Surface

from tuxemon.platform.const import buttons
from tuxemon.platform.platform_pygame.events import (
    DPadButtonInfo,
    DPadInfo,
    DPadRectsInfo,
)
from tuxemon.ui.draw import blit_alpha

if TYPE_CHECKING:
    from tuxemon.platform.events import PlayerInput

logger = logging.getLogger(__name__)

# Grid layout parameters
GRID_COLUMNS = 4
GRID_ROWS = 3
CELL_SIZE = 90
GRID_PADDING = 10

BUTTON_LAYOUT: dict[int, dict[str, Any]] = {
    buttons.A: {"label": "A", "color": (255, 0, 0), "grid": (3, 2)},
    buttons.B: {"label": "B", "color": (0, 0, 255), "grid": (2, 2)},
    buttons.X: {"label": "X", "color": (255, 255, 0), "grid": (1, 2)},
    buttons.Y: {"label": "Y", "color": (0, 255, 255), "grid": (0, 2)},
    buttons.R1: {"label": "R1", "color": (255, 100, 100), "grid": (3, 1)},
    buttons.L1: {"label": "L1", "color": (100, 255, 100), "grid": (0, 1)},
    buttons.R2: {"label": "R2", "color": (255, 150, 150), "grid": (3, 0)},
    buttons.L2: {"label": "L2", "color": (150, 255, 150), "grid": (0, 0)},
    buttons.START: {
        "label": "Start",
        "color": (200, 200, 200),
        "grid": (2, 1),
    },
    buttons.SELECT: {
        "label": "Select",
        "color": (180, 180, 180),
        "grid": (1, 1),
    },
    buttons.BACK: {"label": "Back", "color": (160, 160, 160), "grid": (1, 0)},
}


class InputVisualizer:
    def __init__(self, screen_size: tuple[int, int]) -> None:
        self.screen_size = screen_size
        self.font = Font(None, 24)
        self.dpad_visualizer: DPadInfo = self.create_visual_dpad()
        self.button_visualizers: dict[int, DPadButtonInfo] = {}
        self.load()

        grid_origin = (
            self.screen_size[0] - GRID_COLUMNS * CELL_SIZE - GRID_PADDING,
            self.screen_size[1] - GRID_ROWS * CELL_SIZE - GRID_PADDING,
        )

        for btn, props in BUTTON_LAYOUT.items():
            col, row = props["grid"]
            x = grid_origin[0] + col * CELL_SIZE
            y = grid_origin[1] + row * CELL_SIZE
            self.button_visualizers[btn] = self.create_visual_button(x, y)

    def create_visual_dpad(self) -> DPadInfo:
        return DPadInfo(
            surface=Surface((150, 150)),
            position=(20, self.screen_size[1] - 170),
            rect=DPadRectsInfo(
                up=Rect(70, self.screen_size[1] - 170, 50, 50),
                down=Rect(70, self.screen_size[1] - 120, 50, 50),
                left=Rect(20, self.screen_size[1] - 120, 50, 50),
                right=Rect(120, self.screen_size[1] - 120, 50, 50),
            ),
        )

    def create_visual_button(self, x: int, y: int) -> DPadButtonInfo:
        return DPadButtonInfo(
            surface=Surface((75, 75)),
            position=(x, y),
            rect=Rect(x, y, 75, 75),
        )

    def load(self) -> None:
        pass

    def draw(self, screen: Surface, inputs: Mapping[int, PlayerInput]) -> None:
        # Draw D-pad background
        self.dpad_visualizer.surface.fill((50, 50, 50))
        blit_alpha(
            screen,
            self.dpad_visualizer.surface,
            self.dpad_visualizer.position,
            150,
        )

        # Highlight D-pad directions
        if inputs.get(buttons.UP) and inputs[buttons.UP].held:
            draw.rect(screen, (0, 255, 0), self.dpad_visualizer.rect.up)
        if inputs.get(buttons.DOWN) and inputs[buttons.DOWN].held:
            draw.rect(screen, (0, 255, 0), self.dpad_visualizer.rect.down)
        if inputs.get(buttons.LEFT) and inputs[buttons.LEFT].held:
            draw.rect(screen, (0, 255, 0), self.dpad_visualizer.rect.left)
        if inputs.get(buttons.RIGHT) and inputs[buttons.RIGHT].held:
            draw.rect(screen, (0, 255, 0), self.dpad_visualizer.rect.right)

        # Draw and highlight buttons
        for btn, visualizer in self.button_visualizers.items():
            visualizer.surface.fill((50, 50, 50))
            blit_alpha(screen, visualizer.surface, visualizer.position, 150)

            if inputs.get(btn) and inputs[btn].held:
                color = BUTTON_LAYOUT[btn]["color"]
                draw.circle(
                    screen,
                    color,
                    visualizer.rect.center,
                    visualizer.rect.width // 2,
                )

            label = BUTTON_LAYOUT[btn]["label"]
            text = self.font.render(label, True, (255, 255, 255))
            screen.blit(text, text.get_rect(center=visualizer.rect.center))
