# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_condition import CoreCondition

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.session import Session



        shape_list = (
            self.shapes.split(":") if ":" in self.shapes else [self.shapes]
        )
        return target.shape.slug in shape_list



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
        tag_list = [tag.lower() for tag in self.elements.split(":")]
        monster_tags = [tag.lower() for tag in target.tags]
        # Check if the monster has any of the tags listed in `monster_tags`
        return any(tag in monster_tags for tag in tag_list)



