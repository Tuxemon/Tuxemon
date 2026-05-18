# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon import formula
from tuxemon.core.core_effect import CoreEffect, ItemEffectResult
from tuxemon.database.rules import config_capdev
from tuxemon.db import Acquisition

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session

logger = logging.getLogger(__name__)


@dataclass
class CaptureCombinedEffect(CoreEffect):
    """
    Attempts to capture a target monster using a capture device.

    This effect combines multiple modifiers (status and tuxeball type) to
    determine capture success. It performs a shake check, calculates the
    number of shakes, and applies capture effects if successful.

    **Parameters**

    - ``category``: The capture category (used for device classification).
    - ``label``: The capture device label (e.g. ``xero``, ``omni``).
    - ``lower_bound``: Lower bound modifier applied when type conditions are met.
    - ``upper_bound``: Upper bound modifier applied when type conditions are met.

    **Example**

    .. code-block:: json

        "effects": [
            "capture_combined omni 0.5 1.5"
        ]
    """

    name = "capture_combined"
    category: str
    label: str
    lower_bound: float
    upper_bound: float

    def apply_item_target(
        self, session: Session, item: Item, target: Monster
    ) -> ItemEffectResult:
        self.session = session
        self.client = session.client

        # Calculate status modifier
        status_modifier = formula.calculate_status_modifier(item, target)

        # Calculate tuxeball modifier
        tuxeball_modifier = self._calculate_tuxeball_modifier(target)

        # Perform shake check and capture calculation
        shake_check = formula.shake_check(
            target, status_modifier, tuxeball_modifier
        )
        capture, shakes = formula.capture(shake_check)

        if not capture:
            return ItemEffectResult(name=item.name, num_shakes=shakes)

        # Apply capture effects
        self._apply_capture_effects(item, target)

        return ItemEffectResult(
            name=item.name, success=True, num_shakes=shakes
        )

    def _calculate_tuxeball_modifier(self, target: Monster) -> float:
        """
        Calculate the status effectiveness modifier based on the opponent's
        status.
        """
        capdev_modifier = config_capdev.capdev_modifier
        our_monster = self.client.combat_session.field_monsters.get_monsters(
            self.session.player
        )

        if not our_monster:
            return capdev_modifier

        monster = our_monster[0]

        if not monster.types.current or not monster.types.current:
            return capdev_modifier

        if self.label == "xero":
            return (
                self.upper_bound
                if monster.types.current != target.types.current
                else self.lower_bound
            )
        elif self.label == "omni":
            return (
                self.lower_bound
                if monster.types.current != target.types.current
                else self.upper_bound
            )
        else:
            return capdev_modifier

    def _apply_capture_effects(self, item: Item, target: Monster) -> None:
        if self.session.player.tuxepedia.is_seen(target.slug):
            self.client.combat_session.set_variable("new_tuxepedia", True)
        self.session.player.tuxepedia.register_caught(target.slug)
        target.capture_device = item.slug
        target.wild = False
        target.set_acquisition(Acquisition.CAPTURED)
        self.session.player.party.add_monster(
            target, len(self.session.player.monsters)
        )
