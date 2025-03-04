# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass

from tuxemon.event import MapCondition
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

    name = "has_tech"

    def test(self, session: Session, condition: MapCondition) -> bool:
        player = session.player
        tech = condition.parameters[0]
        if player.has_tech(tech):
            return True
        else:
            return False
