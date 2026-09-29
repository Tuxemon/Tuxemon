# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pygame.surface import Surface


class RenderMixin:
    def draw(self, surface: Surface) -> None:
        """
        Render the state to the surface passed. Must be overloaded in children.

        Do not change the state of any game entities. Every draw should be the
        same for a given game time. Any game changes should be done during
        update.
        """
