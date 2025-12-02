# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tuxemon.technique.technique import Technique


class TechSorter:
    def __init__(self, mode: str = "id") -> None:
        self.mode = mode

    def sort(self, techniques: Sequence[Technique]) -> Sequence[Technique]:
        if self.mode == "name":
            return sorted(techniques, key=lambda t: t.name.lower())
        elif self.mode == "power":
            return sorted(techniques, key=lambda t: t.power, reverse=True)
        else:  # default: id
            return sorted(techniques, key=lambda t: t.tech_id)

    def set_mode(self, mode: str) -> None:
        self.mode = mode
