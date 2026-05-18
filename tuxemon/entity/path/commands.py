# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass

from tuxemon.db import Direction

logger = logging.getLogger(__name__)


@dataclass
class PushCommand:
    direction: Direction
    strength: int


@dataclass
class SpeedCommand:
    modifier: float


@dataclass
class ContinueCommand:
    direction: Direction


@dataclass
class RepathCommand:
    destination: tuple[int, int]
    cooldown: float
    immediate: bool


@dataclass
class StopMovementCommand:
    pass


MovementCommand = (
    PushCommand
    | SpeedCommand
    | ContinueCommand
    | RepathCommand
    | StopMovementCommand
)
