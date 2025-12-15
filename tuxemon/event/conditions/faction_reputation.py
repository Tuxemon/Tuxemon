# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass

from tuxemon.db import SpatialCondition
from tuxemon.event import get_npc
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
        operator: Numeric comparison operator. Accepted values are "less_than",
            "less_or_equal", "greater_than", "greater_or_equal", "equals"
            and "not_equals".
        threshold: A string representation of an integer (e.g. "30", "-100").
            Will be parsed and used as a numeric threshold in comparison.
    """

    name = "faction_reputation"

    def test(self, session: Session, condition: SpatialCondition) -> bool:
        if len(condition.parameters) != 4:
            return False

        character_slug, faction_slug, operator, threshold_raw = (
            condition.parameters
        )
        threshold = int(threshold_raw)

        char = get_npc(session, character_slug)
        if not char:
            logger.error(
                f"[Condition] Character '{character_slug}' not found."
            )
            return False

        faction_manager = session.world.faction_manager
        faction = faction_manager.get(faction_slug)
        if not faction:
            return False

        rep = faction.get_reputation(char.slug)
        comparison = compare(operator, rep, threshold)
        logger.debug(
            f"[Condition] {char.slug}'s rep with {faction_slug}: {rep} vs {operator} {threshold} = {comparison}"
        )
        return comparison
