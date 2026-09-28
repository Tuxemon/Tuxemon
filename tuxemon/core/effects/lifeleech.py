# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
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
    Applies the "lifeleech" status effect.

    This effect drains HP from the host monster and transfers it to the
    linked monster, simulating a leeching effect. The amount transferred
    is determined by dividing the host's HP by the specified divisor.

    **Parameters**

      - ``divisor``: Integer value used to calculate the HP transfer amount.
      - The host's HP is divided by this number to determine how much HP
        is leeched and given to the linked monster.

    **Example**

    .. code-block:: json

        "effects": [
            "lifeleech 3"
        ]
    """

    name = "lifeleech"
    divisor: int

    def apply_status(
        self, session: Session, status: Status
    ) -> StatusEffectResult:
        lifeleech: bool = False
        host = status.host
        linked = status.linked_monster
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
        if linked and linked.is_fainted and status.has_phase(EffectPhase.PERFORM_STATUS):
            host.status.clear_status(session)

        return StatusEffectResult(name=status.name, success=lifeleech)
