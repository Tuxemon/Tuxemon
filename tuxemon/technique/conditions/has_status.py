# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass

from tuxemon.monster import Monster
from tuxemon.technique.techcondition import TechCondition


@dataclass
class HasStatusCondition(TechCondition):
    """
    Checks if the creature has a status or not.

    Parameters:
    -

    Example:
    "conditions": [
        "is has_status status_xxx"
        "not has_status status_xxx"
    ],

    """

    name = "has_status"

    def test(self, target: Monster) -> bool:
        if target.status:
            return True
        else:
            return False
