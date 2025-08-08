# SPDX-License-Identifier: GPL-3.0
# Copyright (c) ...
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_condition import CoreCondition

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.session import Session


@dataclass
class TagCondition(CoreCondition):
    """
    Compares the target Monster's tags against the given tags.

    Returns true if it has at least one of the listed tags.
    """

    name = "tag"
    elements: str  # Colon-separated list of tags to match

    def test_with_monster(self, session: Session, target: Monster) -> bool:
        # Split the colon-separated parameter string into a list
        elements = (
            self.elements.split(":")
            if ":" in self.elements
            else [self.elements]
        )
        # Check if the monster has any of the tags listed in `elements`
        return any(tag in elements for tag in target.tags)
