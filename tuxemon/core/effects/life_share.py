# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session
    from tuxemon.technique.technique import Technique


@dataclass
class LifeShareEffect(CoreEffect):
    """
    Applies the "life_share" effect to a technique.

    This effect redistributes HP between the user and the target based on
    the specified direction and averaging method. It allows monsters to
    share their current HP values in different ways, potentially balancing
    health between them.

    **Parameters**

    - ``direction``: Determines the flow of HP sharing.
      - ``user_to_target``: The user's HP is shared with the target.
      - ``target_to_user``: The target's HP is shared with the user.
    - ``method``: Determines how HP values are averaged.
      - ``weighted``: Weighted average based on each monster's maximum HP.
      - ``geometric``: Geometric mean, favoring lower HP values.
      - ``simple``: Simple arithmetic average of both HP values.

    **Example**

    .. code-block:: json

        "effects": [
            "life_share user_to_target weighted"
        ]
    """

    name = "life_share"
    direction: str
    method: str

    def apply_tech_target(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        hit = session.client.combat_session.get_tech_hit(user)
        tech.hit = tech.accuracy >= hit
        done = False
        if tech.hit:
            source, dest = (
                (user, target)
                if self.direction == "user_to_target"
                else (target, user)
            )
            if not source.is_fainted and not dest.is_fainted:
                if self.method == "weighted":
                    weighted_average(source, dest)
                elif self.method == "geometric":
                    geometric_mean(source, dest)
                else:
                    simple_average(source, dest)
                done = True
        return TechEffectResult(name=tech.name, success=done)


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
