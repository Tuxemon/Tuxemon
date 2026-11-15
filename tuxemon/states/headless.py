# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from pygame.rect import Rect

from tuxemon.state.state import State

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.platform.events import PlayerInput


class HeadlessServerState(State):
    """State for running the game server without graphics."""

    name: ClassVar[str] = "HeadlessServerState"
    rect = Rect((0, 0), (0, 0))
    transparent = True
    force_draw = False

    def __init__(self, client: BaseClient, *args: Any, **kwargs: Any):
        super().__init__(client, *args, **kwargs)

    def process_event(self, event: PlayerInput) -> PlayerInput | None:
        return None
