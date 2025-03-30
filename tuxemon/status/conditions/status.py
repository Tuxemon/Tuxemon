# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.status.statuscondition import StatusCondition

if TYPE_CHECKING:
    from tuxemon.monster import Monster


@dataclass
class CurrentStatusCondition(StatusCondition):
    """
    Checks against the creature's current statuses.
    """

    name = "status"
    expected: str

    def test(self, target: Monster) -> bool:
        return self.expected in [
            x.slug for x in target.status if hasattr(x, "slug")
        ]
