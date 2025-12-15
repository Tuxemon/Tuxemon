# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass

from tuxemon.db import SpatialCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session


@dataclass
class AFKStateCondition(EventCondition):
    """
    Check if one or more AFK states (thresholds) have been met.

    Script usage:
        .. code-block::

            is afk_state <level>

    Examples:
        is afk_state example
        is afk_state warn:kick
    """

    name = "afk_state"

    def test(self, session: Session, condition: SpatialCondition) -> bool:
        afk_manager = session.client.afk_manager
        levels = condition.parameters[0].split(":")
        return any(afk_manager.is_threshold_met(level) for level in levels)
