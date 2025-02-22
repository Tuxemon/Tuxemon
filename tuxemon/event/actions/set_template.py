# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
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

    By using default:
        set_template player,default
    it's going to reassign the default sprite

    Script usage:
        .. code-block::

            set_template <character>,<sprite>[,combat_front]

    Script parameters:
        character: Either "player" or npc slug name (e.g. "npc_maple").
        sprite: must be inside mods/tuxemon/sprites
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

        if self.sprite == "default":
            gender = character.game_variables.get("race_choice", "")
            sprite_mapping = {
                "gender_enby": ("enbyasian", "enbyasian"),
                "gender_whatever": ("penguin", "penguin"),
                "black_female": ("brownheroine_brown", "heroineblack"),
                "black_male": ("adventurerblack", "adventurerblack"),
                "white_female": ("heroine", "heroine"),
                "white_male": ("adventurer", "adventurer"),
            }
            sprite_name, combat_front = sprite_mapping.get(
                gender, (None, None)
            )
            if sprite_name:
                character.template.sprite_name = sprite_name
                if combat_front:
                    character.template.combat_front = combat_front
        else:
            character.template.sprite_name = self.sprite
            logger.info(f"{character.name}'s sprite is {self.sprite}")
            if self.combat_front:
                character.template.combat_front = self.combat_front
                logger.info(f"{character.name}'s front is {self.combat_front}")
        character.sprite_renderer._load_sprites()
