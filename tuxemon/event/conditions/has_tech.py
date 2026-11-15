# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session


@dataclass
class HasTechCondition(EventCondition):
    """
    Check to see if the player has a technique in his party.

    Script usage:
        .. code-block::

            is has_tech <technique>

    Script parameters:
        technique: Technique slug name (e.g. "bullet").
    """

    name: ClassVar[str] = "has_tech"
    technique: str

    def test(self, session: Session) -> bool:
        player = session.player
        if player.party.has_tech(self.technique):
            return True
        else:
            return False
