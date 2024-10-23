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
    Healing effect based on photogenesis or not.

    Parameters:
        start_hour: The hour when the effect starts healing.
        peak_hour: The hour when the effect heals (maximum)
        end_hour: The hour when the effect stops healing.

    eg "photogenesis 18,0,6"
    """

    name = "photogenesis"
    start_hour: int
    peak_hour: int
    end_hour: int

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

        hour = int(player.game_variables.get("hour", 0))
        shape = Shape()
        shape.load(user.shape.value)
        max_multiplier = shape.hp / 2

        multiplier = formula.calculate_time_based_multiplier(
            hour=hour,
            peak_hour=self.peak_hour,
            max_multiplier=max_multiplier,
            start=self.start_hour,
            end=self.end_hour,
        )

        factors = {self.name: multiplier}

        if tech.hit and not self.session.client.map_inside:
            heal = formula.simple_heal(tech, user, factors)
            if heal == 0:
                extra = tech.use_failure
            else:
                if user.current_hp < user.hp:
                    heal_amount = min(heal, user.hp - user.current_hp)
                    user.current_hp += heal_amount
                    done = True
                elif user.current_hp == user.hp:
                    extra = "combat_full_health"
        return {
            "success": done,
            "damage": 0,
            "element_multiplier": 0.0,
            "should_tackle": False,
            "extra": extra,
        }
