# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction


@final
@dataclass
class SetPlayerSpriteAction(EventAction):
    """
    Switch sprite.

    Script usage:
        .. code-block::

            set_player_sprite <sprite>

    """

    name = "set_player_sprite"
    sprite: str

    def start(self) -> None:
        player = self.session.player
        player.player_sprite = self.sprite
        player.load_sprites()
