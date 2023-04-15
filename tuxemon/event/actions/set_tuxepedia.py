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
    monster_slug: str
    status: str

    def start(self) -> None:
        player = self.session.player.tuxepedia
        caught = []
        seen = []
        for key, value in player.items():
            if value == SeenStatus.seen:
                seen.append(key)
            if value == SeenStatus.caught:
                caught.append(key)

        # Append the tuxepedia with a key
        if self.status == SeenStatus.caught:
            if self.monster_slug not in caught:
                player[str(self.monster_slug)] = SeenStatus.caught
        elif self.status == SeenStatus.seen:
            # to avoid setting seen a monster caught
            if self.monster_slug in caught:
                return
            else:
                player[str(self.monster_slug)] = SeenStatus.seen
        else:
            raise ValueError(f"{self.status} must be caught or seen")
