# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from pygame.draw import circle
from pygame.surface import Surface

from tuxemon.platform.const.graphics import RED_COLOR
from tuxemon.state.state import State

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.platform.events import PlayerInput


class SinkState(State):
    """State blocking input to lower states in the stack."""

    name: ClassVar[str] = "SinkState"
    transparent = True

    def __init__(self, client: BaseClient, *args: Any, **kwargs: Any):
        super().__init__(client, *args, **kwargs)

    def process_event(self, event: PlayerInput) -> PlayerInput | None:
        return None

    def draw(self, surface: Surface) -> None:
        indicator_size = 30  # pixels
        # Position: bottom-right corner with a small margin
        x = surface.get_width() - indicator_size - 8
        y = surface.get_height() - indicator_size - 8
        circle(
            surface,
            RED_COLOR,
            (x + indicator_size // 2, y + indicator_size // 2),
            indicator_size // 2,
        )
