# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, StatusEffectResult
from tuxemon.db import EffectPhase
from tuxemon.formula import calculate_hp_transfer

if TYPE_CHECKING:
    from tuxemon.session import Session
    from tuxemon.status.status import Status

logger = logging.getLogger(__name__)


@dataclass
class LifeLeechEffect(CoreEffect):
    """
    This effect has a chance to apply the lifeleech status effect.

    Parameters:
        user: The monster getting HPs.
        target: The monster losing HPs.
        divisor: The number by which target HP is to be divided.
    """

    name = "lifeleech"
    divisor: int

    def apply_status(
        self, session: Session, status: Status
    ) -> StatusEffectResult:
        lifeleech: bool = False
        host = status.get_host()
        linked = status.get_linked_monster()
        if (
            status.has_phase(EffectPhase.PERFORM_STATUS)
            and linked
            and not linked.is_fainted
        ):
            damage = calculate_hp_transfer(linked, host, self.divisor)
            logger.debug(
                f"[LifeLeech] {linked.name} leeched {damage} HP from {host.name}"
            )
            host.current_hp = max(0, host.current_hp - damage)
            linked.current_hp = min(linked.hp, linked.current_hp + damage)
            lifeleech = True
        if linked and linked.is_fainted:
            host.status.clear_status(session)

        return StatusEffectResult(name=status.name, success=lifeleech)
