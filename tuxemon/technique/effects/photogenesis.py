# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from tuxemon import formula
from tuxemon.shape import Shape
from tuxemon.technique.techeffect import TechEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.technique.technique import Technique


class PhotogenesisEffectResult(TechEffectResult):
    pass


@dataclass
class PhotogenesisEffect(TechEffect):
    """
    Healing is based on healing power (photogenesis).
    """

    name = "photogenesis"
    objective: str

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> PhotogenesisEffectResult:
        player = user.owner
        extra: Optional[str] = None
        done: bool = False
        assert player

        tech.hit = tech.accuracy >= (
            tech.combat_state._random_tech_hit.get(user, 0.0)
            if tech.combat_state
            else 0.0
        )

        mon = user if self.objective == "user" else target
        hour = int(player.game_variables.get("hour", 0))
        shape = Shape()
        shape.load(mon.shape.value)
        max_multiplier = shape.hp / 2

        multiplier = calculate_multiplier(
            hour=hour,
            peak_hour=12,
            max_multiplier=max_multiplier,
            start=6,
            end=18,
        )

        factors = {self.name: multiplier}

        if tech.hit and not self.session.client.map_inside:
            heal = formula.simple_heal(tech, mon, factors)
            if heal == 0:
                extra = "solar_synthesis_fail"
            else:
                if mon.current_hp < mon.hp:
                    heal_amount = min(heal, mon.hp - mon.current_hp)
                    mon.current_hp += heal_amount
                    done = True
                elif mon.current_hp == mon.hp:
                    extra = "combat_full_health"
        return {
            "success": done,
            "damage": 0,
            "element_multiplier": 0.0,
            "should_tackle": False,
            "extra": extra,
        }


def calculate_multiplier(
    hour: int,
    peak_hour: int,
    max_multiplier: float,
    start: int,
    end: int,
) -> float:
    """
    Calculate the multiplier based on the given hour and peak hour.

    Args:
        hour: The current hour.
        peak_hour: The peak hour.
        max_multiplier: The maximum power.
        start: The start hour of the period.
        end: The end hour of the period.

    Returns:
        float: The calculated multiplier.
    """
    if end < start:
        end += 24
    if hour < start:
        hour += 24
    if peak_hour < start:
        peak_hour += 24

    if start <= hour < end:
        distance_from_peak = abs(hour - peak_hour)
        if distance_from_peak > (end - start) / 2:
            distance_from_peak = (end - start) - distance_from_peak
        weighted_power = max_multiplier * (
            1 - (distance_from_peak / ((end - start) / 2)) ** 2
        )
        return max(weighted_power, 0.0)
    else:
        return 0.0
