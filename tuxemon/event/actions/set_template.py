# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction

logger = logging.getLogger(__name__)


@final
@dataclass
class SetTemplateAction(EventAction):
    """
    Switch template (sprite and combat_front).

    Please remember that if you change the combat_front,
    automatically will change the combat_back.

    Eg if you put xxx, it's going to be xxx_back.png

    if you choose a feminine sprite, then it's advisable:
        heroine
    if you choose a masculine sprite, then it's advisable:
        adventurer

    Script usage:
        .. code-block::

            set_template <character>,<sprite>[,combat_front]

    Script parameters:
        character: Either "player" or npc slug name (e.g. "npc_maple").
        sprite: must be inside mods/tuxemon/sprites (default = original)
        eg: adventurer_brown_back.png -> adventurer
        combat_front: must be inside mods/tuxemon/gfx/sprites/player
        eg: adventurer.png -> adventurer

    """

    name = "set_template"
    character: str
    sprite: str
    combat_front: Optional[str] = None

    def start(self) -> None:
        character = get_npc(self.session, self.character)
        if character is None:
            logger.error(f"{self.character} not found")
            return

        if character.template:
            character.template[0].sprite_name = self.sprite
            logger.info(f"{character.name}'s sprite is {self.sprite}")
            if self.combat_front:
                character.template[0].combat_front = self.combat_front
                logger.info(f"{character.name}'s front is {self.combat_front}")
        character.load_sprites()
