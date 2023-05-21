# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.technique.techeffect import TechEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.technique.technique import Technique


class DefaultEffectResult(TechEffectResult):
    pass


@dataclass
class DefaultEffect(TechEffect):
    """
    Default allows techniques without effects to manifest.

    """

    name = "default"

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> DefaultEffectResult:
        return {"success": True}
