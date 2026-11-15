# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

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

    name: ClassVar[str] = "afk_state"
    level: str

    def test(self, session: Session) -> bool:
        afk_manager = session.client.afk_manager
        levels = self.level.split(":")
        return any(afk_manager.is_threshold_met(level) for level in levels)
