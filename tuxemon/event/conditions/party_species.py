# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session
from tuxemon.tools import compare


@dataclass
class PartySpeciesCondition(EventCondition):
    """
    Compare the number of different species in the player's team.

    Script usage:
        .. code-block::

            is party_species <operator>,<count>

    Script parameters:
        operator: Numeric comparison operator. Accepted values are "less_than",
            "less_or_equal", "greater_than", "greater_or_equal", "equals"
            and "not_equals".
        count: Number of different species to compare with.

    eg. "is party_species greater_or_equal,3": the team holds at least 3
    different species.
    """

    name: ClassVar[str] = "party_species"
    operator: str
    count: int

    def test(self, session: Session) -> bool:
        species = {monster.slug for monster in session.player.monsters}
        return compare(self.operator, len(species), int(self.count))
