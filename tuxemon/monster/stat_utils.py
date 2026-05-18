# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from typing import TYPE_CHECKING

from tuxemon.db import StatModel
from tuxemon.tools import ops_dict

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster.monster import Monster
    from tuxemon.status.status import Status
    from tuxemon.technique.technique import Technique

logger = logging.getLogger(__name__)

NONLINEAR_TABLE = {
    -6: 2 / 8,
    -5: 2 / 7,
    -4: 2 / 6,
    -3: 2 / 5,
    -2: 2 / 4,
    -1: 2 / 3,
    0: 1.0,
    1: 3 / 2,
    2: 4 / 2,
    3: 5 / 2,
    4: 6 / 2,
    5: 7 / 2,
    6: 8 / 2,
}


def apply_stat_modifiers(
    host: Monster,
    source: Item | Technique | Status,
    stat_modifiers: dict[str, StatModel],
) -> None:

    for stat_slug, stat_model in stat_modifiers.items():
        if not stat_model:
            continue

        logger.debug(
            f"[StatChange] Applying modifier to '{stat_slug}' "
            f"(step={stat_model.step}, value={stat_model.value}, "
            f"mode={stat_model.scaling_mode})"
        )

        step_delta = stat_model.step
        raw_value = stat_model.value
        max_dev = stat_model.max_deviation
        override = stat_model.overridetofull
        scaling_mode = stat_model.scaling_mode
        max_step_limit = int(stat_model.max_step_limit)

        # HP override
        if stat_slug == "current_hp" and override:
            logger.debug(
                f"[StatChange] HP override → restoring to full ({host.hp})"
            )
            host.current_hp = host.hp
            continue

        # Base stat
        if stat_slug == "current_hp":
            base = host.current_hp
        else:
            base = getattr(host.base_stats, stat_slug)

        logger.debug(f"[StatChange] Base value for '{stat_slug}' = {base}")

        # STEP-BASED LOGIC
        if step_delta is not None:
            actual_step = (
                random.randint(step_delta - max_dev, step_delta + max_dev)
                if max_dev
                else step_delta
            )

            logger.debug(
                f"[StatChange] Step delta={step_delta}, deviation={max_dev}, "
                f"actual_step(before clamp)={actual_step}"
            )

            actual_step = max(
                -max_step_limit, min(max_step_limit, actual_step)
            )

            old_stage = getattr(
                source.temporary_stat_boosts, f"{stat_slug}_stage", 0
            )

            new_stage = max(
                -max_step_limit, min(max_step_limit, old_stage + actual_step)
            )

            logger.debug(
                f"[StatChange] Old stage={old_stage}, new stage={new_stage}"
            )

            setattr(
                source.temporary_stat_boosts, f"{stat_slug}_stage", new_stage
            )

            if scaling_mode == "linear":
                multiplier = 1 + (new_stage / max_step_limit)
            else:
                multiplier = NONLINEAR_TABLE[int(new_stage)]

            logger.debug(
                f"[StatChange] Scaling mode={scaling_mode}, multiplier={multiplier}"
            )

            new_value = int(base * multiplier)
            boost_value = new_value - base

        # VALUE-BASED LOGIC
        else:
            applied_value = (
                random.randint(
                    int(raw_value - max_dev), int(raw_value + max_dev)
                )
                if max_dev
                else raw_value
            )

            logger.debug(
                f"[StatChange] Value-based: raw={raw_value}, deviation={max_dev}, "
                f"applied={applied_value}, op={stat_model.operation}"
            )

            op_func = ops_dict.get(stat_model.operation, lambda a, b: a)
            new_value = round(op_func(base, applied_value))
            boost_value = new_value - base

        # Clamp non-HP stats
        if stat_slug != "current_hp" and new_value <= 0:
            logger.debug(
                f"[StatChange] Clamping '{stat_slug}' to minimum value 1 "
                f"(computed {new_value})"
            )
            new_value = 1
            boost_value = 1 - base

        # Apply result
        if stat_slug == "current_hp":
            clamped_hp = max(0, min(new_value, host.hp))
            logger.debug(
                f"[StatChange] HP change: {host.current_hp} → {clamped_hp}"
            )
            host.current_hp = clamped_hp
        else:
            logger.debug(
                f"[StatChange] Final boost for '{stat_slug}' = {boost_value}"
            )
            setattr(source.temporary_stat_boosts, stat_slug, int(boost_value))
