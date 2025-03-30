# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from typing import Final, Optional

import pygame

from tuxemon.platform.const import buttons
from tuxemon.platform.events import PlayerInput

_EVENT_MAP: Final = {
    buttons.UP: pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP),
    buttons.DOWN: pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN),
    buttons.LEFT: pygame.event.Event(pygame.KEYDOWN, key=pygame.K_LEFT),
    buttons.RIGHT: pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT),
    buttons.BACK: pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE),
    buttons.A: pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN),
    buttons.B: pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE),
}


def playerinput_to_event(event: PlayerInput) -> Optional[pygame.event.Event]:
    return _EVENT_MAP.get(event.button)
