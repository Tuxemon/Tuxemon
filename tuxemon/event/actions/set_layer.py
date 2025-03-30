# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, final

from tuxemon import prepare
from tuxemon.event.eventaction import EventAction
from tuxemon.graphics import string_to_colorlike
from tuxemon.states.world.worldstate import WorldState


@final
@dataclass
class SetLayerAction(EventAction):
    """
    Allows to change the color of the transparent layer.

    Script usage:
        .. code-block::

            set_layer <rgb>

    Script parameters:
        rgb: color (eg red > 255,0,0,128 > 255:0:0:128)
            default transparent

    Note: this is not a separate state, so it's advisable
        to add a 4th value to the rgb, if not you're not
        going to see the character, ideally 128.

    """

    name = "set_layer"
    rgb: Optional[str] = None

    def start(self) -> None:
        transparent = prepare.TRANSPARENT_COLOR
        rgb = string_to_colorlike(self.rgb) if self.rgb else transparent
        world = self.session.client.get_state_by_name(WorldState)
        world.map_renderer.layer_color = rgb
