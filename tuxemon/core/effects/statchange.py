# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, StatusEffectResult
from tuxemon.db import EffectPhase, StatType
from tuxemon.tools import ops_dict

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.session import Session
    from tuxemon.status.status import Status

logger = logging.getLogger(__name__)


@dataclass
class StatChangeEffect(CoreEffect):
    """
    Applies a stat-altering effect to a target monster during combat.

    This effect modifies one or more combat-relevant stats on a monster, either
    through value-based operations (e.g., add/subtract) or step-based scaling,
    depending on configuration. Step-based changes allow incremental percentage
    adjustments relative to a stat's base value, with clamping via `max_step_limit`
    to ensure balance.

    Stats are pulled from the status's stat components (e.g. `status.statmelee`, etc.),
    and can impact either permanent base stats or runtime health values.

    This class supports:
    - Optional randomness via `max_deviation`
    - HP overrides using `overridetofull`, which resets current HP to max HP
    - Clamping of final values to avoid death or stat corruption

    Effect Trigger:
        - Only applies if the status has phase `PERFORM_STATUS`

    JSON SYNTAX (per stat object inside Status):
    {
        "value": float,             # Direct stat adjustment (ignored if using step)
        "step": int,                # Optional step delta (e.g., +2 steps to speed); used in scaling
        "max_deviation": int,       # Optional random deviation applied to step or value
        "max_step_limit": float,    # Max cumulative scaling boundary (e.g., ±0.5 for ±50% total change)
        "scaling_mode": str,        # "linear" uses base*(1 + step), "nonlinear" uses tiered multipliers
        "operation": str,           # Arithmetic operation: "add", "subtract", "divide" (for value logic only)
        "overridetofull": bool      # If True and stat is HP, fully restores current HP to max
    }

    Stats Supported:
        - speed
        - armour
        - melee
        - ranged
        - dodge
        - hp         > modifies base_stats.hp
        - current_hp > modifies runtime health

    Attributes:
        name: Effect name, used for identification and serialization.

    Returns:
        StatusEffectResult: Indicates whether the stat change was successful
        and contains the status name.
    """

    name = "statchange"

    def apply_status_target(
        self, session: Session, status: Status, target: Monster
    ) -> StatusEffectResult:
        statsmaster = [
            status.statspeed,
            status.stathp,
            status.statarmour,
            status.statmelee,
            status.statranged,
            status.statdodge,
        ]
        slugs = [
            "speed",
            "current_hp",  # special case for current HP
            "armour",
            "melee",
            "ranged",
            "dodge",
        ]

        if (
            status.has_phase(EffectPhase.PERFORM_STATUS)
            and self.name not in status._effect_applied
        ):
            status._effect_applied.add("statchange")
            for stat_model, slug in zip(statsmaster, slugs):
                if not stat_model:
                    continue

                step_delta = stat_model.step
                raw_value = stat_model.value
                max_dev = stat_model.max_deviation
                override = stat_model.overridetofull
                operation = stat_model.operation

                # Handle HP override
                if slug == "current_hp" and override:
                    target.current_hp = target.hp
                    logger.info(
                        f"[{status.name}] Overriding current HP > {target.name}: {target.hp}"
                    )
                    continue

                new_value = 0

                if step_delta is not None:
                    scaling_mode = stat_model.scaling_mode
                    max_step = stat_model.max_step_limit

                    actual_step = (
                        random.randint(
                            step_delta - max_dev, step_delta + max_dev
                        )
                        if max_dev
                        else step_delta
                    )

                    # Clamp actual step to allowable range
                    actual_step = int(
                        max(-max_step, min(max_step, actual_step))
                    )

                    if slug == "current_hp":
                        base = target.hp
                    else:
                        base = getattr(target.base_stats, slug)

                    current = target.return_stat(StatType(slug))
                    old_step = (current - base) / base
                    total_step = max(
                        -max_step,
                        min(max_step, old_step + actual_step),
                    )

                    if scaling_mode == "linear":
                        new_value = int(base * (1 + total_step))
                    else:
                        # Nonlinear tiered formula
                        if total_step > 0:
                            new_value = int(
                                base * (max_step + total_step) / max_step
                            )
                        else:
                            new_value = int(
                                base * max_step / (max_step - total_step)
                            )

                    logger.debug(
                        f"[{status.name}] {slug} changed via {scaling_mode} step on {target.name}: "
                        f"step {old_step:.3f} > {total_step:.3f}, value {current:.2f} > {new_value:.2f}"
                    )

                else:
                    # Value-based logic
                    applied_value = (
                        random.randint(
                            int(raw_value - max_dev), int(raw_value + max_dev)
                        )
                        if max_dev
                        else raw_value
                    )

                    stat_base = (
                        getattr(target, slug)
                        if slug == "current_hp"
                        else getattr(target.base_stats, slug, None)
                    )
                    if stat_base is None:
                        continue

                    op_func = ops_dict.get(operation, lambda a, b: a)
                    new_value = int(op_func(stat_base, applied_value))

                    logger.debug(
                        f"[{status.name}] {slug} changed via value on {target.name}: "
                        f"{stat_base} > {new_value}"
                    )

                # Safety: Clamp stat values
                if new_value <= 0 and slug != "current_hp":
                    new_value = 1

                # Assignment
                if slug == "current_hp":
                    target.current_hp = min(new_value, target.hp)
                elif slug in StatType.__members__:
                    setattr(target.base_stats, slug, int(new_value))

        elif status.has_phase(EffectPhase.ON_END):
            target.set_stats()

        return StatusEffectResult(name=status.name, success=True)
