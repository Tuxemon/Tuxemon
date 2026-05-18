# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon import formula
from tuxemon.core.core_effect import CoreEffect, ItemEffectResult
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session

VALID_METHODS = {"capture", "doll", "food"}


@dataclass
class ParkEffect(CoreEffect):
    """
    Applies the "park" effect to an item.

    This effect handles special item interactions within the park system,
    such as capturing monsters, using dolls, or offering food. The behavior
    depends on the specified ``method``.

    **Parameters**

      - ``method``: Determines the type of park interaction.
      - ``capture``: Attempts to capture the target monster using formulas
        for status, device modifiers, and shake checks.
      - ``doll``: Applies item modifiers to the encounter, typically affecting
        monster behavior.
      - ``food``: Applies item modifiers to the encounter, typically making
        monsters easier to approach or capture.

    **Example**

    .. code-block:: json

        "effects": [
            "park capture"
        ]
    """

    name = "park"
    method: str

    def apply_item_target(
        self, session: Session, item: Item, target: Monster
    ) -> ItemEffectResult:
        self.extras: list[str] = []
        self.session = session
        self.client = session.client
        if self.method == "capture":
            return self._capture(item, target)
        elif self.method == "doll":
            return self._doll(item, target)
        elif self.method == "food":
            return self._food(item, target)
        else:
            raise ValueError(
                f"Invalid method '{self.method}'. Must be one of {VALID_METHODS}."
            )

    def _doll(self, item: Item, target: Monster) -> ItemEffectResult:
        encounter = self.session.client.park_session.encounters.get(
            target.slug
        )
        if encounter:
            encounter.apply_item_modifiers(item)
        return ItemEffectResult(name=item.name, success=True)

    def _food(self, item: Item, target: Monster) -> ItemEffectResult:
        encounter = self.session.client.park_session.encounters.get(
            target.slug
        )
        if encounter:
            encounter.apply_item_modifiers(item)
        return ItemEffectResult(name=item.name, success=True)

    def _capture(self, item: Item, target: Monster) -> ItemEffectResult:
        status_modifier = formula.calculate_status_modifier(item, target)

        tuxeball_modifier = formula.calculate_capdev_modifier(
            item, target, self.session.player
        )

        shake_check = formula.shake_check(
            target, status_modifier, tuxeball_modifier
        )
        capture, shakes = formula.capture(shake_check)

        if not capture:
            self._handle_capture_failure(item, target)
            return ItemEffectResult(name=item.name, num_shakes=shakes)

        self._apply_capture_effects(item, target)
        self.session.client.park_session.archive_encounter(target.slug)
        return ItemEffectResult(
            name=item.name, success=True, num_shakes=shakes
        )

    def _handle_capture_failure(self, item: Item, target: Monster) -> None:
        formula.on_capture_fail(item, target, self.session.player)
        labels = [
            "menu_park_afraid",
            "menu_park_stare",
            "menu_park_wander",
            "menu_park_resting",
            "menu_park_playful",
            "menu_park_alert",
        ]
        empty = Technique.create("empty")
        empty.use_tech = random.choice(labels)
        self.session.client.combat_session.action_queue.rewrite(target, empty)
        self.session.client.park_session.record_failure()

    def _apply_capture_effects(self, item: Item, target: Monster) -> None:
        formula.on_capture_success(item, target, self.session.player)

        if self.session.player.tuxepedia.is_seen(target.slug):
            self.client.combat_session.set_variable("new_tuxepedia", True)
        self.session.player.tuxepedia.register_caught(target.slug)
        target.capture_device = item.slug
        target.wild = False
        self.session.player.party.add_monster(
            target, len(self.session.player.monsters)
        )
        self.session.client.park_session.record_capture()
