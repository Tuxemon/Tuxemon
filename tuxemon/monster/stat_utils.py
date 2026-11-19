# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.db import StatModel
from tuxemon.monster.stats import NONLINEAR_TABLE, stage_multiplier
from tuxemon.tools import ops_dict

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster.monster import Monster
    from tuxemon.status.status import Status
    from tuxemon.technique.technique import Technique

logger = logging.getLogger(__name__)

__all__ = [
    "NONLINEAR_TABLE",
    "StageChange",
    "apply_stat_modifiers",
    "get_source_key",
    "stage_multiplier",
]


@dataclass(frozen=True)
class StageChange:
    """
    A stage a modifier actually moved, for reporting back to the player.

    ``steps`` is what the step limit allowed, not what was asked for, so a
    stat already at the cap reports nothing rather than a change nobody
    would see.
    """

    stat: str
    steps: int


def get_source_key(source: Item | Technique | Status) -> str:
    """
    Identifies the object responsible for a temporary boost.

    Boosts are stored on the affected monster, so they need a key telling
    apart the sources that applied them. Two uses of the same item (or two
    hits of the same technique) share a key and therefore stack their
    stages, the way repeated applications always have.
    """
    slug = getattr(source, "slug", type(source).__name__)
    return f"{type(source).__name__.lower()}:{slug}"


def apply_stat_modifiers(
    host: Monster,
    source: Item | Technique | Status,
    stat_modifiers: dict[str, StatModel],
) -> list[StageChange]:
    """
    Applies a source's stat modifiers to a monster.

    Returns the stages that actually moved, in the order they were
    applied, so the caller can tell the player what changed. Value-based
    modifiers move no stage and so report nothing.
    """
    source_key = get_source_key(source)
    stage_changes: list[StageChange] = []

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
        is_current_hp = stat_slug == "current_hp"
        if is_current_hp:
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

            # Runtime health has no stage to accumulate: the step lands
            # on the current value once, there and then.
            if is_current_hp:
                multiplier = stage_multiplier(
                    actual_step, scaling_mode, max_step_limit
                )
                _set_current_hp(host, round(base * multiplier))
                continue

            old_stage = host.temporary_stat_boosts.get_stage(stat_slug)
            new_stage = host.temporary_stat_boosts.add_stage(
                source_key,
                stat_slug,
                actual_step,
                scaling_mode,
                max_step_limit,
            )

            # The boost itself is derived from the stage on read, so that
            # every source raising this stat shares one stage.
            logger.debug(
                f"[StatChange] Step {actual_step:+d} on '{stat_slug}' "
                f"→ stage {new_stage} (mode={scaling_mode})"
            )

            if new_stage != old_stage:
                stage_changes.append(
                    StageChange(stat_slug, new_stage - old_stage)
                )
            continue

        # VALUE-BASED LOGIC
        applied_value = (
            random.randint(int(raw_value - max_dev), int(raw_value + max_dev))
            if max_dev
            else raw_value
        )

        logger.debug(
            f"[StatChange] Value-based: raw={raw_value}, deviation={max_dev}, "
            f"applied={applied_value}, op={stat_model.operation}"
        )

        op_func = ops_dict.get(stat_model.operation, lambda a, b: a)
        new_value = round(op_func(base, applied_value))

        if is_current_hp:
            _set_current_hp(host, new_value)
            continue

        # Clamp non-HP stats
        if new_value <= 0:
            logger.debug(
                f"[StatChange] Clamping '{stat_slug}' to minimum value 1 "
                f"(computed {new_value})"
            )
            new_value = 1

        boost_value = new_value - base
        logger.debug(
            f"[StatChange] Final boost for '{stat_slug}' = {boost_value}"
        )
        host.temporary_stat_boosts.add_flat(
            source_key, stat_slug, int(boost_value)
        )

    return stage_changes


def _set_current_hp(host: Monster, value: int) -> None:
    clamped_hp = max(0, min(value, host.hp))
    logger.debug(f"[StatChange] HP change: {host.current_hp} → {clamped_hp}")
    host.current_hp = clamped_hp
