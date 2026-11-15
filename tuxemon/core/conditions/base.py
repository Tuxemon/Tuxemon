# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_condition import CoreCondition
from tuxemon.tools import check_condition, parse_flag

if TYPE_CHECKING:
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session
    from tuxemon.technique.technique import Technique


@dataclass
class BaseCondition(CoreCondition):
    """
    Evaluates a Monster or Technique against specified attributes.

    **Parameters**
    - ``source``: The attribute set to check (e.g. ``tags``, ``types``, ``shape``, ``terrains``, ``species``).
    - ``options``: A colon-separated list of expected values or negations (e.g. ``water:!fire``).
    - ``match``: Flag determining evaluation mode. ``"true"`` requires all conditions to match, ``"false"`` requires any.

    **Returns**
    - ``True`` if the target's attributes satisfy the given options.
    - ``False`` otherwise.

    **Example**

    .. code-block:: json

        "conditions": [
            "is base types water:!fire"
        ]
    """

    name = "base"
    source: str  # e.g., "tags", "types", "shapes", "terrains"
    options: str  # e.g., "water:!fire"
    match: str = "false"  # "true" for all, "false" for any

    def get_dataset_monster(self, target: Monster) -> set[str]:
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

        else:
            raise ValueError(f"Unsupported source: {self.source}")

    def get_dataset_technique(self, target: Technique) -> set[str]:
        """
        Extracts a set of normalized strings from the target based on the source.
        """
        if self.source == "tags":
            return {tag.strip().lower() for tag in target.tags}

        elif self.source == "types":
            return {ele.slug.strip().lower() for ele in target.types.current}

        else:
            raise ValueError(f"Unsupported source: {self.source}")

    def _test_conditions(self, base: set[str]) -> bool:
        conditions = [opt.strip().lower() for opt in self.options.split(":")]
        match_all = parse_flag(self.match)
        results = [check_condition(opt, base) for opt in conditions]
        return all(results) if match_all else any(results)

    def test_with_monster(self, session: Session, target: Monster) -> bool:
        return self._test_conditions(self.get_dataset_monster(target))

    def test_with_tech(self, session: Session, target: Technique) -> bool:
        return self._test_conditions(self.get_dataset_technique(target))
