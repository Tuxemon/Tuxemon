# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction


@final
@dataclass
class ClearTuxepediaAction(EventAction):
    """
    Clear the key and value in the Tuxepedia dictionary.

    Script usage:
        .. code-block::

            clear_tuxepedia <monster_slug>

    Script parameters:
        monster_slug: Monster slug name (e.g. "rockitten").

    """

    name = "clear_tuxepedia"
    monster_key: str

    def start(self) -> None:
        player = self.session.player
        player.tuxepedia.pop(self.monster_key)
