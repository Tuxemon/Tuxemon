# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from pygame.rect import Rect
from pygame.surface import Surface

from tuxemon.sprite import Sprite

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tuxemon.entity.npc import NPC


class CombatTextDisplay:
    """Handles the drawing of dynamic text labels (Name, Level, Status)
    onto a monster's HUD sprite image."""

    def __init__(
        self,
        get_rect_func: Callable[[Any, str], Rect],
        shadow_text_func: Callable[[str], Surface],
    ) -> None:
        self._get_rect = get_rect_func
        self._shadow_text = shadow_text_func

    def draw_text(
        self,
        hud: Sprite,
        owner: NPC,
        label_data: dict[str, str],
    ) -> None:
        """Draws the provided text data onto the HUD sprite image."""
        if hud.base_image is None:
            return

        hud.image.blit(hud.base_image, (0, 0))

        line1_rect = self._get_rect(owner, "hud_line1")
        line2_rect = self._get_rect(owner, "hud_line2")

        hud.image.blit(self._shadow_text(label_data["line1"]), line1_rect)
        if label_data["line2"]:
            hud.image.blit(self._shadow_text(label_data["line2"]), line2_rect)
