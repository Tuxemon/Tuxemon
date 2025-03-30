# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event.eventaction import EventAction


@final
@dataclass
class ClearTuxepediaAction(EventAction):
    """
    Clear the key and value in the Tuxepedia dictionary. If the
    monster_slug parameter is missing, this action will completely
    reset the Tuxepedia dictionary by removing all seen monsters.

    If the monster_slug parameter is provided, this action will remove
    the specified monster from the Tuxepedia dictionary.

    Script usage:
        .. code-block::

            clear_tuxepedia <monster_slug>

    Script parameters:
        monster_slug: Monster slug name (e.g. "rockitten").

    """

    name = "clear_tuxepedia"
    monster_key: Optional[str] = None

    def start(self) -> None:
        player = self.session.player
        if self.monster_key is None:
            player.tuxepedia.reset()
        else:
            player.tuxepedia.remove_entry(self.monster_key)
