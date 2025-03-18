# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

from tuxemon import formula, prepare
from tuxemon.db import CategoryStatus as Category
from tuxemon.db import SeenStatus
from tuxemon.item.itemeffect import ItemEffect, ItemEffectResult
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster import Monster

logger = logging.getLogger(__name__)


@dataclass
class CaptureEffect(ItemEffect):
    """Attempts to capture the target."""

    name = "capture"

    def apply(
        self, item: Item, target: Union[Monster, None]
    ) -> ItemEffectResult:
        assert target

        # Calculate status modifier
        status_modifier = self._calculate_status_modifier(target)

        # Calculate tuxeball modifier
        tuxeball_modifier = self._calculate_tuxeball_modifier(item, target)

        # Perform shake check and capture calculation
        shake_check = formula.shake_check(
            target, status_modifier, tuxeball_modifier
        )
        capture, shakes = formula.capture(shake_check)

        if not capture:
            self._handle_capture_failure(item, target)
            return ItemEffectResult(
                name=item.name, success=False, num_shakes=shakes, extras=[]
            )

        # Apply capture effects
        self._apply_capture_effects(item, target)

        return ItemEffectResult(
            name=item.name, success=True, num_shakes=shakes, extras=[]
        )

    def _calculate_status_modifier(self, target: Monster) -> float:
        status_modifier = prepare.STATUS_MODIFIER
        if target.status and target.status[0].category:
            status_modifier = (
                prepare.STATUS_NEGATIVE
                if target.status[0].category == Category.negative
                else prepare.STATUS_POSITIVE
            )
        return status_modifier

    def _calculate_tuxeball_modifier(
        self, item: Item, target: Monster
    ) -> float:
        tuxeball_modifier = prepare.TUXEBALL_MODIFIER

        if item.slug == "tuxeball_crusher":
            crusher = ((target.armour / 5) * 0.01) + 1
            if crusher >= 1.4:
                crusher = 1.4
            if (
                self._calculate_status_modifier(target)
                == prepare.STATUS_POSITIVE
            ):
                crusher = 0.01
            tuxeball_modifier = crusher
        elif item.slug == "tuxeball_ancient":
            tuxeball_modifier = 99.0
        elif item.slug == "tuxeball_noble":
            tuxeball_modifier = 1.25
        elif item.slug == "tuxeball_lavish":
            tuxeball_modifier = 1.5
        elif item.slug == "tuxeball_grand":
            tuxeball_modifier = 1.75
        elif item.slug == "tuxeball_majestic":
            tuxeball_modifier = 2.0

        return tuxeball_modifier

    def _handle_capture_failure(self, item: Item, target: Monster) -> None:
        assert item.combat_state
        if item.slug == "tuxeball_park":
            empty = Technique()
            empty.load("empty")
            _wander = "spyder_park_wander"
            label = self.user.game_variables.get(item.slug, _wander)
            empty.use_tech = label
            item.combat_state._action_queue.rewrite(target, empty)

    def _apply_capture_effects(self, item: Item, target: Monster) -> None:
        assert item.combat_state
        if item.slug == "tuxeball_candy":
            target.level += 1
        elif item.slug == "tuxeball_hardened":
            tuxeball = self.user.find_item(item.slug)
            if tuxeball:
                tuxeball.quantity -= 1

        if self.user.tuxepedia.is_seen(target.slug):
            item.combat_state._new_tuxepedia = True
        self.user.tuxepedia.add_entry(target.slug, SeenStatus.caught)
        target.capture_device = item.slug
        target.wild = False
        self.user.add_monster(target, len(self.user.monsters))
