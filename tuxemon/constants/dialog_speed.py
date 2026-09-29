# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

DIALOG_SPEED_PROFILES = {
    "slow": 0.05,
    "fast": 0.015,
    "max": 0.0,
    "urgent": 0.01,
    "sassy": 0.04,
    "whisper": 0.08,
}


def resolve_character_delay(speed_name: str) -> float:
    return DIALOG_SPEED_PROFILES.get(speed_name, DIALOG_SPEED_PROFILES["slow"])
