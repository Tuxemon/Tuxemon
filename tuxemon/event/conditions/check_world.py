# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import ClassVar

from tuxemon.event.eventcondition import EventCondition
from tuxemon.graphics import string_to_colorlike
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@dataclass
class CheckWorldCondition(EventCondition):
    """
    Evaluates specific world conditions against expected values.

    This condition can check various parameters of the game world, such as
    overlay colors (layer) and speech bubbles (bubble).

    Script usage:
        .. code-block::

            check_world <parameter>,<value>

    Script parameters:
        parameter: The name of the world attribute to check.
        value: The expected value to compare against.

    Examples:
        - "check_world layer"
          Ensures the overlay color is empty.

        - "check_world bubble,npc_maple"
          Checks if NPC "npc_maple" currently has a speech bubble.
    """

    name: ClassVar[str] = "check_world"
    param: str
    value: str | None = None

    def test(self, session: Session) -> bool:
        if self.param == "layer":
            if self.value is None:
                return True
            rgb = string_to_colorlike(self.value)
            return session.client.map_renderer.layer_color == rgb
        if self.param == "bubble":
            if self.value is None:
                return False
            char = session.client.get_npc(self.value)
            if char is None:
                logger.error(f"{self.value} not found")
                return False
            return session.client.map_renderer.bubble_manager.has_bubble(char)
        return False
