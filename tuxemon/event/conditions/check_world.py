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
    Check some world's parameter against a given value.

    Script usage:
        .. code-block::

            check_world <parameter>,<value>

    Script parameters:
        parameter: Name of the parameter to check (eg. "layer", etc.).
        value: Given value to check.

    layer: color value which is used to overlay the world
    bubble: speech bubble of an npc

    eg. "check_world layer,255:255:255:0"

    """

    name = "check_world"

    def test(self, session: Session, condition: MapCondition) -> bool:
        world = session.client.get_state_by_name(WorldState)
        params = condition.parameters
        if params[0] == "layer":
            rgb = string_to_colorlike(params[1])
            return world.map_renderer.layer_color == rgb
        if params[0] == "bubble":
            char = get_npc(session, params[1])
            if char is None:
                logger.error(f"{params[1]} not found")
                return False
            return char in world.map_renderer.bubble
        return False
