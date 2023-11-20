# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.technique.technique import Technique


@final
@dataclass
class OverwriteTechAction(EventAction):
    """
    Overwrite / replace a technique with another.

    Script usage:
        .. code-block::

            overwrite_tech <removed>,<added>

    Script parameters:
        removed: Instance id (name variable).
        added: Slug technique.

    eg. "overwrite_tech name_variable,peck"

    """

    name = "overwrite_tech"
    removed: str
    added: str

    def overwrite(self, removed: Technique) -> None:
        slot = self.monster.moves.index(removed)
        added = Technique()
        added.load(self.added)
        self.monster.moves.remove(removed)
        self.monster.moves.insert(slot, added)

    def start(self) -> None:
        self.player = self.session.player
        # look for the technique
        tech_id = uuid.UUID(
            self.player.game_variables[self.removed],
        )
        for mon in self.player.monsters:
            technique = mon.find_tech_by_id(tech_id)
            if technique:
                self.monster = mon
                self.overwrite(technique)
