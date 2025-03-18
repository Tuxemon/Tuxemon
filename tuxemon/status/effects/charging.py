# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.status.status import Status
from tuxemon.status.statuseffect import StatusEffect, StatusEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster


@dataclass
class ChargingEffect(StatusEffect):
    """
    Charging status

    """

    name = "charging"

    def apply(self, status: Status, target: Monster) -> StatusEffectResult:
        player = target.owner
        assert player
        _statuses: list[Status] = []
        if status.phase == "perform_action_tech":
            target.status.clear()
            if status.repl_tech:
                cond = Status()
                cond.load(status.repl_tech)
                cond.steps = player.steps
                cond.link = target
                _statuses = [cond]
        if status.phase == "perform_action_item":
            target.status.clear()
            if status.repl_item:
                cond = Status()
                cond.load(status.repl_item)
                cond.steps = player.steps
                cond.link = target
                _statuses = [cond]
        return StatusEffectResult(
            name=status.name,
            success=True,
            statuses=_statuses,
            techniques=[],
            extras=[],
        )
