# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import ClassVar

from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session
from tuxemon.tools import compare

logger = logging.getLogger(__name__)


@dataclass
class FactionReputationCondition(EventCondition):
    """
    Checks if an NPC's reputation meets a threshold.

    Script usage:
        .. code-block::

            is faction_reputation <character>,<faction_slug>,<operator>,<threshold>

    Script parameters:
        character: Either "player" or npc slug name (e.g. "npc_maple").
        faction: Faction slug.
        operator: Numeric comparison operator. Accepted values are "less_than",
            "less_or_equal", "greater_than", "greater_or_equal", "equals"
            and "not_equals".
        threshold: A string representation of an integer (e.g. "30", "-100").
            Will be parsed and used as a numeric threshold in comparison.
    """

    name: ClassVar[str] = "faction_reputation"
    character: str
    faction: str
    operator: str
    threshold: int

    def test(self, session: Session) -> bool:
        char = session.client.get_npc(self.character)
        if not char:
            logger.error(
                f"[Condition] Character '{self.character}' not found."
            )
            return False

        faction_manager = session.world.faction_manager
        faction = faction_manager.get(self.faction)
        if not faction:
            return False

        rep = faction.get_reputation(char.slug)
        comparison = compare(self.operator, rep, self.threshold)
        logger.debug(
            f"[Condition] {char.slug}'s rep with {self.faction}: {rep} vs {self.operator} {self.threshold} = {comparison}"
        )
        return comparison
