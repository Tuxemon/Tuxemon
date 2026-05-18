# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from collections.abc import Callable
from typing import Final

import pygame
from pygame.event import Event

from tuxemon.platform.const import buttons
from tuxemon.platform.events import PlayerInput

_EVENT_MAP: Final[dict[int, Callable[[], Event]]] = {
    buttons.UP: lambda: Event(pygame.KEYDOWN, key=pygame.K_UP),
    buttons.DOWN: lambda: Event(pygame.KEYDOWN, key=pygame.K_DOWN),
    buttons.LEFT: lambda: Event(pygame.KEYDOWN, key=pygame.K_LEFT),
    buttons.RIGHT: lambda: Event(pygame.KEYDOWN, key=pygame.K_RIGHT),
    buttons.BACK: lambda: Event(pygame.KEYDOWN, key=pygame.K_ESCAPE),
    buttons.A: lambda: Event(pygame.KEYDOWN, key=pygame.K_RETURN),
    buttons.B: lambda: Event(pygame.KEYDOWN, key=pygame.K_ESCAPE),
}


def playerinput_to_event(event: PlayerInput) -> Event | None:
    factory = _EVENT_MAP.get(event.button)
    if not factory:
        return None
    return factory()
