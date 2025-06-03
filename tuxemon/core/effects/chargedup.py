# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import StatusEffect, StatusEffectResult
from tuxemon.status.status import Status

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.session import Session


@dataclass
class ChargedUpEffect(StatusEffect):
    """
    Charged up status

    """

    name = "chargedup"

    def apply(
        self, session: Session, status: Status, target: Monster
    ) -> StatusEffectResult:
        player = target.owner
        assert player
        _statuses: list[Status] = []
        if status.phase == "perform_action_tech":
            target.status.clear()
            if status.repl_tech:
                cond = Status.create(status.repl_tech)
                cond.steps = player.steps
                cond.link = target
                _statuses = [cond]
        return StatusEffectResult(
            name=status.name, success=True, statuses=_statuses
        )
