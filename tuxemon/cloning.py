# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""Sampling kits: a net, a vial and a field cloner in one pack.

When the net holds, the vial takes a sample and the cloner grows a copy on
the spot. The copy joins the player; the wild monster goes free.
"""

from __future__ import annotations

from tuxemon.db import Acquisition
from tuxemon.monster.monster import Monster
from tuxemon.time_handler import today_month_day

# Saved fields a fresh clone does not inherit from the wild monster.
_NOT_COPIED = ("instance_id", "status", "mother_iid", "father_iid")


def make_clone(wild: Monster) -> Monster:
    """
    Grow a copy of ``wild``: same species, level, moves, gender and hidden
    stats, but a new individual at full health with no status.
    """
    state = {
        key: value
        for key, value in wild.get_state().items()
        if key not in _NOT_COPIED
    }
    clone = Monster.from_save(state)
    clone.wild = False
    clone.current_hp = clone.hp
    clone.capture_date = today_month_day()
    clone.set_acquisition(Acquisition.CLONED)
    return clone
