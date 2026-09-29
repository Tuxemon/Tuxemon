# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class SetAppearanceLayerAction(EventAction):
    """
    Change a layered appearance field (outfit, accessory, palette).

    Script usage:

        .. code-block:: text

           set_appearance_layer <character>,<layer>,<value>

    Script parameters:

        character:
            Either "player" or npc slug name (e.g. "npc_maple").

        layer:
            One of: outfit, accessory, palette, combat_sheet.

        value:
            The sprite filename (without extension) to apply to the layer.
            Example: jacket_red, hat_blue, palette_dark.
    """

    name = "set_appearance_layer"
    character: str
    layer: str
    value: str | None = None

    def start(self, session: Session) -> None:
        target = session.client.get_npc(self.character)
        if not target:
            logger.error(f"NPC {self.character} not found")
            self.stop()
            return

        if self.layer not in (
            "outfit",
            "accessory",
            "palette",
            "combat_sheet",
        ):
            logger.error(f"Invalid appearance layer '{self.layer}'")
            self.stop()
            return

        setattr(target.appearance_manager.state, self.layer, self.value)
        target.sprite_controller.update_appearance(
            target.appearance_manager.state
        )

        logger.info(f"Updated {target.name} {self.layer} to {self.value}")
