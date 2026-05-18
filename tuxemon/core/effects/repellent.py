# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, ItemEffectResult
from tuxemon.step_tracker import StepTracker

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.session import Session

logger = logging.getLogger(__name__)


@dataclass
class RepellentEffect(CoreEffect):
    """
    Applies the "repellent" effect to an item.

    This effect prevents wild encounters for a specified number of steps
    after the item is used. It works by registering a step tracker that
    counts down until the repellent expires.

    **Parameters**

    - ``steps``: Float value representing how many steps the repellent
      will last before wearing off.

    **Example**

    .. code-block:: json

        "effects": [
            "repellent 1000"
        ]
    """

    name = "repellent"
    steps: float

    def apply_item(self, session: Session, item: Item) -> ItemEffectResult:
        player = session.player
        current_steps = round(player.steps)

        player.step_tracker.add_tracker(
            self.name,
            StepTracker(
                steps=current_steps, countdown=self.steps, milestones=[]
            ),
        )

        logger.info(
            f"Applied repellent from '{item.name}' to '{player.name}' for {self.steps} steps."
        )
        return ItemEffectResult(success=True)
