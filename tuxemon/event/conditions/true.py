# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass

from tuxemon.event import MapCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session


@dataclass
class TrueCondition(EventCondition):
    """
    This condition always returns true.

    Script usage:
        .. code-block::

            is true

    """

    name = "true"

    def test(self, session: Session, condition: MapCondition) -> bool:
        return True
