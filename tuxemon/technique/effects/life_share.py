# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.combat import fainted
from tuxemon.technique.techeffect import TechEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.technique.technique import Technique


@dataclass
class LifeShareEffect(TechEffect):
    """
    Shares the current HP amounts of the two monsters.

    The direction of the sharing is determined by the `direction` attribute,
    which can be either "user_to_target" or "target_to_user".

    The method of the sharing is determined by the `method` attribute,
    which can be either "weighted", "geometric" or "simple".
    """

    name = "life_share"
    direction: str
    method: str

    def apply(
        self, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        tech.hit = tech.accuracy >= (
            tech.combat_state._random_tech_hit.get(user, 0.0)
            if tech.combat_state
            else 0.0
        )
        done = False
        if tech.hit:
            source, dest = (
                (user, target)
                if self.direction == "user_to_target"
                else (target, user)
            )
            if not fainted(source) and not fainted(dest):
                if self.method == "weighted":
                    weighted_average(source, dest)
                elif self.method == "geometric":
                    geometric_mean(source, dest)
                else:
                    simple_average(source, dest)
                done = True
        return TechEffectResult(
            name=tech.name,
            success=done,
            damage=0,
            element_multiplier=0.0,
            should_tackle=False,
            extras=[],
        )


def weighted_average(source: Monster, dest: Monster) -> None:
    """
    Calculate the weighted average of two HP values, taking into account the
    maximum HP of each monster.
    """
    weighted_sum = (source.current_hp * source.hp) + (
        dest.current_hp * dest.hp
    )
    average = weighted_sum / (source.hp + dest.hp)
    source.current_hp = min(int(average), source.hp)
    dest.current_hp = min(int(average), dest.hp)


def geometric_mean(source: Monster, dest: Monster) -> None:
    """
    Calculate the geometric mean of two HP values, giving more weight to
    the lower HP value.
    """
    average = math.sqrt(source.current_hp * dest.current_hp)
    source.current_hp = min(int(average), source.hp)
    dest.current_hp = min(int(average), dest.hp)


def simple_average(source: Monster, dest: Monster) -> None:
    """
    Calculate the simple average of two HP values.
    """
    average = (source.current_hp + dest.current_hp) / 2
    source.current_hp = min(int(average), source.hp)
    dest.current_hp = min(int(average), dest.hp)
