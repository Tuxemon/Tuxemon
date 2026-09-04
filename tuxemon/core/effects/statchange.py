# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import (
    CoreEffect,
    ItemEffectResult,
    StatusEffectResult,
    TechEffectResult,
)
from tuxemon.db import EffectPhase
from tuxemon.locale.locale import T
from tuxemon.monster.stat_utils import (
    StageChange,
    apply_stat_modifiers,
    get_source_key,
)

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session
    from tuxemon.status.status import Status
    from tuxemon.technique.technique import Technique

logger = logging.getLogger(__name__)

GREAT_CHANGE = 2


def stage_change_message_key(steps: int) -> str:
    """
    The message describing a stage change of this size.

    Two stages or more is the difference between "rose" and "rose
    greatly", matching the step a single Boost item grants.
    """
    if steps > 0:
        return (
            "combat_state_stat_rose_greatly"
            if steps >= GREAT_CHANGE
            else "combat_state_stat_rose"
        )
    return (
        "combat_state_stat_fell_greatly"
        if steps <= -GREAT_CHANGE
        else "combat_state_stat_fell"
    )


def describe_stage_changes(
    monster: Monster, stage_changes: Sequence[StageChange]
) -> list[str]:
    """Tells the player which of a monster's stats moved, and how far."""
    messages = []
    for change in stage_changes:
        if not change.steps:
            continue
        params = {
            "target": monster.name,
            "stat": T.translate(change.stat),
        }
        messages.append(
            T.format(stage_change_message_key(change.steps), params)
        )
    return messages


@dataclass
class StatChangeEffect(CoreEffect):
    """
    Applies the "statchange" status effect.

    This effect modifies one or more combat-relevant stats of a monster
    during battle. Changes can be applied either through direct value-based
    operations (e.g., add, subtract, divide) or through step-based scaling
    relative to the stat's base value. Step-based scaling supports clamping
    via ``max_step_limit`` to maintain balance.

    **Supported Stats**
    - ``speed``
    - ``armour``
    - ``melee``
    - ``ranged``
    - ``dodge``
    - ``hp`` → modifies permanent base HP
    - ``current_hp`` → modifies runtime health

    **Parameters (per stat modifier)**
    - ``value``: Float, direct adjustment applied to the stat (ignored if ``step`` is used).
    - ``step``: Integer, step delta for scaling (e.g., +2 steps to speed).
    - ``max_deviation``: Optional integer, adds randomness to ``step`` or ``value``.
    - ``max_step_limit``: Float, maximum cumulative scaling boundary (e.g., ±0.5 for ±50%).
    - ``scaling_mode``: String, either ``linear`` (base * (1 + step)) or ``nonlinear`` (tiered multipliers).
    - ``operation``: String, arithmetic operation for value logic (``add``, ``subtract``, ``divide``).
    - ``overridetofull``: Boolean, if ``True`` and stat is HP, restores current HP to maximum.

    **Example**

    .. code-block:: json

        "effects": [
            "statchange"
        ]

        "stat_modifiers": {
            "speed": {
                "step": 2,
                "max_deviation": 1,
                "max_step_limit": 0.5,
                "scaling_mode": "linear"
            },
            "current_hp": {
                "overridetofull": true
            }
        }
    """

    name = "statchange"
    objectives: str = ""

    def apply_status(
        self, session: Session, status: Status
    ) -> StatusEffectResult:
        host = status.host

        if status.has_phase(
            EffectPhase.ON_START
        ) and not status.is_already_applied(self.name):
            apply_stat_modifiers(host, status, status.stat_modifiers)
            status.mark_applied(self.name)
        elif status.has_phase(EffectPhase.ON_END):
            host.temporary_stat_boosts.withdraw(get_source_key(status))

        return StatusEffectResult(name=status.name, success=True)

    def apply_tech_target(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        if not self.objectives:
            return TechEffectResult(name=tech.name)

        # Rolled the same way "give" rolls for a status, so a stat change
        # delivered by a technique is as reliable as that technique is, and
        # misses alongside its damage rather than landing regardless.
        potency = random.random()
        hit = session.client.combat_session.get_tech_hit(user)
        if tech.potency < potency or tech.accuracy < hit:
            return TechEffectResult(name=tech.name)

        monsters = session.client.combat_session.get_target_monsters(
            self.objectives.split(":"), user, target
        )
        extras = []
        for monster in monsters:
            stage_changes = apply_stat_modifiers(
                monster, tech, tech.stat_modifiers
            )
            extras.extend(describe_stage_changes(monster, stage_changes))

        return TechEffectResult(name=tech.name, success=True, extras=extras)

    def apply_item_target(
        self, session: Session, item: Item, target: Monster
    ) -> ItemEffectResult:
        stage_changes = apply_stat_modifiers(target, item, item.stat_modifiers)
        return ItemEffectResult(
            name=item.name,
            success=True,
            extras=describe_stage_changes(target, stage_changes),
        )
