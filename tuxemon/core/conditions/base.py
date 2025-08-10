# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_condition import CoreCondition
from tuxemon.tools import check_condition, parse_flag

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.session import Session


@dataclass
class BaseCondition(CoreCondition):
    """
    Generic condition evaluator for monster attributes.

    Compares values from a specified source (e.g., 'tags', 'types')
    against the given options.
    """

    name = "base"
    source: str  # e.g., "tags", "types", "shapes", "terrains"
    options: str  # e.g., "water:!fire"
    match: str = "false"  # "true" for all, "false" for any

    def get_dataset(self, target: Monster) -> set[str]:
        """
        Extracts a set of normalized strings from the target based on the source.
        """
        if self.source == "tags":
            return {tag.strip().lower() for tag in target.tags}

        elif self.source == "types":
            return {ele.slug.strip().lower() for ele in target.types.current}

        elif self.source == "shape":
            return {target.shape.slug.strip().lower()}  # Single-element set

        elif self.source == "terrains":
            return {terrain.strip().lower() for terrain in target.terrains}

        elif self.source == "species":
            return {target.species.strip().lower()}

        raise ValueError(f"Unsupported source: {self.source}")

    def test_with_monster(self, session: Session, target: Monster) -> bool:
        base = self.get_dataset(target)
        conditions = [opt.strip().lower() for opt in self.options.split(":")]
        match_all = parse_flag(self.match)
        results = [check_condition(opt, base) for opt in conditions]
        return all(results) if match_all else any(results)
