# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.technique.techcondition import TechCondition

if TYPE_CHECKING:
    from tuxemon.monster import Monster


@dataclass
class StatusCondition(TechCondition):
    """
    Checks against the creature's current statuses.

    """

    name = "status"
    status: str

    def test(self, target: Monster) -> bool:
        return self.status in [
            x.slug for x in target.status if hasattr(x, "slug")
        ]
