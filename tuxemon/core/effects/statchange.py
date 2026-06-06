# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import (
    CoreEffect,
    ItemEffectResult,
    StatusEffectResult,
    TechEffectResult,
)
from tuxemon.db import EffectPhase
from tuxemon.monster.stat_utils import apply_stat_modifiers
from tuxemon.monster.stats import BasicStats

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session
    from tuxemon.status.status import Status
    from tuxemon.technique.technique import Technique

logger = logging.getLogger(__name__)


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
            status.temporary_stat_boosts = BasicStats()

        return StatusEffectResult(name=status.name, success=True)

    def apply_tech_target(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        t = tech.target

        if t["own_monster"]:
            apply_stat_modifiers(user, tech, tech.stat_modifiers)

        if t["enemy_monster"]:
            apply_stat_modifiers(target, tech, tech.stat_modifiers)

        if t["own_team"]:
            for mon in session.client.combat_session.get_own_monsters(user):
                apply_stat_modifiers(mon, tech, tech.stat_modifiers)

        if t["enemy_team"]:
            for mon in session.client.combat_session.get_own_monsters(target):
                apply_stat_modifiers(mon, tech, tech.stat_modifiers)

        if t["own_trainer"]:
            for mon in session.client.combat_session.get_party(user):
                apply_stat_modifiers(mon, tech, tech.stat_modifiers)

        if t["enemy_trainer"]:
            for mon in session.client.combat_session.get_party(target):
                apply_stat_modifiers(mon, tech, tech.stat_modifiers)

        return TechEffectResult(name=tech.name, success=True)

    def apply_item_target(
        self, session: Session, item: Item, target: Monster
    ) -> ItemEffectResult:
        apply_stat_modifiers(target, item, item.stat_modifiers)
        return ItemEffectResult(name=item.name, success=True)
