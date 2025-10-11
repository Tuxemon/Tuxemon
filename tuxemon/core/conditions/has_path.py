# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_condition import CoreCondition

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.session import Session


@dataclass
class HasPathCondition(CoreCondition):
    """
    Checks whether the creature has an evolution path that includes the specified
    item slug.
    """

    name = "has_path"
    expected: str

    def test_with_monster(self, session: Session, target: Monster) -> bool:
        return any(
            self.expected in (evo.item or {}) for evo in target.evolutions
        )
