# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, ItemEffectResult
from tuxemon.monster.monster import Monster
from tuxemon.status.status import Status

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.session import Session


@dataclass
class DieEffect(CoreEffect):
    """
    Applies one random status from a predefined list to the target monster.

    This effect is typically triggered by held items such as ``Die``, which
    grant a random condition (e.g. ``enraged`` or ``sniping``) when combat begins.

    **Parameters**

    - ``statuses``: A colon-separated string of status slugs
      (e.g. ``"enraged:sniping"``).

    **Example**

    .. code-block:: json

        "effects": [
            "die enraged:sniping"
        ]
    """

    name = "die"
    statuses: str

    def apply_item_target(
        self, session: Session, item: Item, target: Monster
    ) -> ItemEffectResult:
        if session.client.combat_session.turn == 1:
            statuses = self.statuses.split(":")
            status_slug = random.choice(statuses)
            status = Status.create(status_slug, target, target.steps)
            result = target.status.apply_status(session, status)
            if result.applied:
                event_bus = session.client.event_bus
                event_bus.publish("status_applied")
                event_bus.publish("update_party_hud")
        return ItemEffectResult(name=item.name, success=True)
