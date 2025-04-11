# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_condition import CoreCondition

if TYPE_CHECKING:
    from tuxemon.monster import Monster


@dataclass
class HasPathCondition(CoreCondition):
    """
    Checks against the creature's evolution paths.

    Accepts a single parameter and returns whether it is applied.

    """

    name = "has_path"
    expected: str

    def test_with_monster(self, target: Monster) -> bool:
        return any(t.item == self.expected for t in target.evolutions)
