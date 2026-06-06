# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.graphics import load_and_scale, string_to_colorlike
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class SetLayerAction(EventAction):
    """
    Change the transparent overlay drawn over the world map each frame.

    The overlay can be a solid/semi-transparent colour or a pre-made image
    (e.g. a torchlight vignette).  Passing no argument clears the overlay.

    Script usage:
        .. code-block::

            set_layer [<value>]

    Script parameters:
        value: One of:

            * An RGBA colour – ``R,G,B,A`` or ``R:G:B:A``
              (e.g. ``255:0:0:128`` for semi-transparent red).
              Default: transparent.
            * An image path relative to the mod root
              (e.g. ``gfx/ui/overlay/torchlight.png``).
            * Omitted or ``none`` – clears the overlay.

    Note: this is not a separate state, so it's advisable to add a 4th
    value to the RGB; without it the character won't be visible
    (ideally 128).
    """

    name = "set_layer"
    rgb: str | None = None

    def start(self, session: Session) -> None:
        renderer = session.client.map_renderer

        if not self.rgb or self.rgb.lower() == "none":
            renderer.layer_color = None
            renderer.layer_image = False
            renderer.layer.fill((0, 0, 0, 0))
            return

        if self.rgb.endswith(".png"):
            try:
                img = load_and_scale(self.rgb)
            except Exception:
                logger.error(f"set_layer: could not load image '{self.rgb}'")
                return
            renderer.layer = img
            renderer.layer_color = None
            renderer.layer_image = True
        else:
            renderer.layer_color = string_to_colorlike(self.rgb)
            renderer.layer_image = False
