# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.db import SeenStatus
from tuxemon.event.eventaction import EventAction


@final
@dataclass
class SetTuxepediaAction(EventAction):
    """
    Set the key and value in the Tuxepedia dictionary.

    Script usage:
        .. code-block::

            set_tuxepedia <monster_slug>,<string>

    Script parameters:
        monster_slug: Monster slug name (e.g. "rockitten").
        string: seen / caught

    """

    name = "set_tuxepedia"
    monster_key: str
    monster_str: str

    def start(self) -> None:
        player = self.session.player.tuxepedia

        # Append the tuxepedia with a key
        if self.monster_str == "caught":
            player[str(self.monster_key)] = SeenStatus.caught
        elif self.monster_str == "seen":
            player[str(self.monster_key)] = SeenStatus.seen
