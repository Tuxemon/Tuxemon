# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass

from tuxemon.event import MapCondition, get_npc
from tuxemon.event.eventcondition import EventCondition
from tuxemon.graphics import string_to_colorlike
from tuxemon.session import Session
from tuxemon.states.world.worldstate import WorldState

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

    name = "check_world"

    def test(self, session: Session, condition: MapCondition) -> bool:
        world = session.client.get_state_by_name(WorldState)
        params = condition.parameters
        if params[0] == "layer":
            if len(params) > 1:
                rgb = string_to_colorlike(params[1])
                return world.map_renderer.layer_color == rgb
            return True
        if params[0] == "bubble":
            if len(params) < 2:
                return False
            char = get_npc(session, params[1])
            if char is None:
                logger.error(f"{params[1]} not found")
                return False
            return char in world.map_renderer.bubble
        return False
