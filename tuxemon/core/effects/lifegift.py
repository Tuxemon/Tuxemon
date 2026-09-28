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
class LifeGiftEffect(CoreEffect):
    """
    Applies the "lifegift" status effect.

    This effect transfers HP from a linked monster to the host monster,
    simulating a gift of life energy. The amount transferred is determined
    by dividing the linked monster's HP by the specified divisor.

    **Parameters**

      - ``divisor``: Integer value used to calculate the HP transfer amount.
      - The linked monster's HP is divided by this number to determine
        how much HP is gifted.

    **Example**

    .. code-block:: json

        "effects": [
            "lifegift 2"
        ]
    """

    name = "lifegift"
    divisor: int

    def apply_status(
        self, session: Session, status: Status
    ) -> StatusEffectResult:
        lifegift: bool = False
        host = status.host
        linked = status.linked_monster
        if (
            status.has_phase(EffectPhase.PERFORM_STATUS)
            and linked
            and not linked.is_fainted
        ):
            damage = calculate_hp_transfer(linked, host, self.divisor)
            logger.debug(
                f"[LifeGift] {linked.name} gifted {damage} HP to {host.name}"
            )
            linked.current_hp = max(0, linked.current_hp - damage)
            host.current_hp = min(host.hp, host.current_hp + damage)
            lifegift = True
        if linked and linked.is_fainted and status.has_phase(EffectPhase.PERFORM_STATUS):
            host.status.clear_status(session)

        return StatusEffectResult(name=status.name, success=lifegift)
