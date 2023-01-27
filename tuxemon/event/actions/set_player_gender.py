# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.db import GenderType
from tuxemon.event.eventaction import EventAction


@final
@dataclass
class SetPlayerGenderAction(EventAction):
    """
    Switch gender.

    Script usage:
        .. code-block::

            set_player_gender <gender>

    """

    name = "set_player_gender"
    gender: str

    def start(self) -> None:
        player = self.session.player
        if self.gender == GenderType.male:
            player.player_gender = GenderType.male
            player.load_sprites()
        elif self.gender == GenderType.female:
            player.player_gender = GenderType.female
            player.load_sprites()
        else:
            raise ValueError(
                f"{self.gender} is invalid, must be male or female",
            )
