# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from tuxemon import formula
from tuxemon.condition.condeffect import CondEffect, CondEffectResult
from tuxemon.locale import T

if TYPE_CHECKING:
    from tuxemon.condition.condition import Condition
    from tuxemon.monster import Monster


class RecoverEffectResult(CondEffectResult):
    pass


@dataclass
class RecoverEffect(CondEffect):
    """
    This effect has a chance to apply the recovering status effect.
    """

    name = "recover"

    def apply(self, tech: Condition, target: Monster) -> RecoverEffectResult:
        extra: Optional[str] = None
        healing: bool = False
        if tech.phase == "perform_action_status":
            if tech.slug == "status_recover":
                user = tech.link
                assert user
                heal = formula.simple_recover(user)
                user.current_hp += heal
                healing = bool(heal)
        if tech.phase == "check_party_hp":
            if tech.slug == "status_recover":
                # check for recover (completely healed)
                if target.current_hp >= target.hp:
                    target.status.clear()
                    # avoid "overcome" hp bar
                    if target.current_hp > target.hp:
                        target.current_hp = target.hp
                    extra = T.format(
                        "combat_state_recover_failure",
                        {
                            "target": target.name.upper(),
                        },
                    )

        return {
            "success": healing,
            "condition": None,
            "technique": None,
            "extra": extra,
        }
