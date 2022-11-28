from __future__ import annotations

from dataclasses import dataclass

from tuxemon.monster import Monster
from tuxemon.technique.techcondition import TechCondition


@dataclass
class StatusCondition(TechCondition):
    """
    Checks against the creature's current statuses.

    Parameters:
    status: Slug of the status

    Example:
    "conditions": [
        "status target,status_xxx"
    ],

    """

    name = "status"
    status: str

    def test(self, target: Monster) -> bool:
        return self.status in [
            x.slug for x in target.status if hasattr(x, "slug")
        ]
