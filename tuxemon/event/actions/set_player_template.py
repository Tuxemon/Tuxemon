# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Union, final

from tuxemon.event.eventaction import EventAction

logger = logging.getLogger(__name__)


@final
@dataclass
class SetPlayerTemplateAction(EventAction):
    """
    Switch template (sprite and combat_front).

    Please remember that if you change the combat_front,
    automatically will change the combat_back.

    Eg if you put xxx, it's going to add xxx_back.png

    if you choose a feminine sprite, then it's advisable:
        heroine
    if you choose a masculine sprite, then it's advisable:
        adventurer

    Script usage:
        .. code-block::

            set_player_template <sprite>[,combat_front]

    Script parameters:
        sprite: must be inside mods/tuxemon/sprites (default = original)
        eg: adventurer_brown_back.png -> adventurer
        combat_front: must be inside mods/tuxemon/gfx/sprites/player
        eg: adventurer.png -> adventurer

    """

    name = "set_player_template"
    sprite: str
    combat_front: Union[str, None] = None

    def start(self) -> None:
        player = self.session.player
        for ele in player.template:
            # repristinate default sprite (gender_choice)
            if self.sprite == "default":
                if player.game_variables["gender_choice"] == "gender_male":
                    ele.sprite_name = "adventurer"
                elif player.game_variables["gender_choice"] == "gender_female":
                    ele.sprite_name = "heroine"
                else:
                    ele.sprite_name = player.game_variables["gender_choice"]
            else:
                ele.sprite_name = self.sprite
                logger.info(f"{player.name} sprite is: {self.sprite}")
            if self.combat_front is not None:
                ele.combat_front = self.combat_front
                logger.info(
                    f"{player.name} combat_front is: {self.combat_front}"
                )
        player.load_sprites()
