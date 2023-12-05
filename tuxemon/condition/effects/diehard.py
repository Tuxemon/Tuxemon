# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from tuxemon.condition.condeffect import CondEffect, CondEffectResult
from tuxemon.locale import T

if TYPE_CHECKING:
    from tuxemon.condition.condition import Condition
    from tuxemon.monster import Monster


class DieHardEffectResult(CondEffectResult):
    pass


@dataclass
class DieHardEffect(CondEffect):
    """
    DieHard status

    """

    name = "diehard"

    def apply(
        self, condition: Condition, target: Monster
    ) -> DieHardEffectResult:
        extra: Optional[str] = None
        if condition.phase == "check_party_hp" and condition.slug == "diehard":
            if target.current_hp <= 0:
                target.current_hp = 1
                target.status.clear()
                extra = T.format(
                    "combat_state_diehard_tech",
                    {
                        "target": target.name.upper(),
                    },
                )
            elif target.current_hp == 1:
                target.status.clear()
                extra = T.format(
                    "combat_state_diehard_end",
                    {
                        "target": target.name.upper(),
                    },
                )

        return {
            "success": True,
            "condition": None,
            "technique": None,
            "extra": extra,
        }
