# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.status.statuscondition import StatusCondition

if TYPE_CHECKING:
    from tuxemon.monster import Monster


@dataclass
class HasStatusCondition(StatusCondition):
    """
    Checks if the creature has a status or not.

    """

    name = "has_status"

    def test(self, target: Monster) -> bool:
        if target.status:
            return True
        else:
            return False
