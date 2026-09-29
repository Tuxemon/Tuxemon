# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from tuxemon.entity.behavior.base import (
    BehaviorPolicy,
    PatrolBehavior,
    WanderBehavior,
)

BEHAVIOR_REGISTRY: dict[str, Callable[..., BehaviorPolicy]] = {
    "patrol": PatrolBehavior,
    "wander": WanderBehavior,
}


def create_behavior(name: str | None, **kwargs: Any) -> BehaviorPolicy | None:
    if not name:
        return None
    factory = BEHAVIOR_REGISTRY.get(name)
    if not factory:
        return None
    return factory(**kwargs)
