# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tuxemon.technique.technique import Technique


class TechSorter:
    def __init__(
        self, attribute: str | None = None, reverse: bool = False
    ) -> None:
        self.attribute = attribute or "tech_id"
        self.reverse = reverse

    def sort(self, techniques: Sequence[Technique]) -> Sequence[Technique]:
        return sorted(
            techniques,
            key=lambda tech: getattr(tech, self.attribute, 0),
            reverse=self.reverse,
        )

    def set_sort_attribute(
        self, attribute: str, reverse: bool = False
    ) -> None:
        self.attribute = attribute
        self.reverse = reverse
