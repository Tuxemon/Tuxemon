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
class SetTemplateAction(EventAction):
    """
    Switch template (sprite and combat_sheet).

    By using default:

        set_template player,default

    it's going to reassign the default sprite.

    Script usage:

        .. code-block:: text

            set_template <character>,<sprite>[,combat_sheet]

    Script parameters:

        character:
            Either "player" or npc slug name (e.g. "npc_maple").

        sprite:
            Must be inside mods/tuxemon/sprites.
            Example: adventurer_brown_back.png -> adventurer.

        combat_sheet:
            Must be inside mods/tuxemon/gfx/sprites/player.
            Example: adventurer.png -> adventurer.

    Note:
        This action only changes the base template fields (sprite_name and
        combat_sheet). Layered appearance fields such as outfit, accessory,
        or palette are handled separately.
    """

    name = "set_template"
    character: str
    sprite: str
    combat_sheet: str | None = None

    def start(self, session: Session) -> None:
        target = session.client.get_npc(self.character)
        if not target:
            logger.error(f"NPC {self.character} not found")
            self.stop()
            return

        if self.sprite == "default":
            target.appearance_manager.reset_to_default()
        else:
            target.appearance_manager.update(self.sprite, self.combat_sheet)
            logger.info(f"Updated {target.name} appearance to {self.sprite}")
