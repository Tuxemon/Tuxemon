# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.monster import Flair


@final
@dataclass
class SetMonsterFlairAction(EventAction):
    """
    Set a monster's flair to the given value.

    Script usage:
        .. code-block::

            set_monster_flair <slot>,<category>,<flair>

    Script parameters:
        slot: Slot of the monster in the party.
        category: Category of the monster flair.
        flair: Name of the monster flair.

    """

    name = "set_monster_flair"
    slot: int
    category: str
    flair: str

    def start(self) -> None:
        monster = self.session.player.monsters[self.slot]
        if self.category in monster.flairs:
            monster.flairs[self.category] = Flair(
                self.category,
                self.flair,
            )
