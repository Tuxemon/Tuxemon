# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, ItemEffectResult

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.session import Session


class BivouacStage(Enum):
    SETUP = 1
    REST = 2
    HEAL = 3
    DONE = 4


@dataclass
class BivouacEffect(CoreEffect):
    """
    Simulates a monster resting at a bivouac (temporary camp).

    This effect progresses through multiple stages (``SETUP``, ``REST``, ``HEAL``, ``DONE``)
    to fully restore a monster's health and clear any status conditions.

    **Stages**
    - ``SETUP``: Initial preparation, locks player controls.
    - ``REST``: Resting period before healing begins.
    - ``HEAL``: Restores health and removes status effects, then unlocks controls.
    - ``DONE``: Marks the effect as finished.

    **Example**

    .. code-block:: json

        "effects": [
            "bivouac"
        ]
    """

    name = "bivouac"
    stage: BivouacStage = BivouacStage.SETUP
    _elapsed: float = 0.0
    _duration: float = 0.0
    _finished: bool = False

    def apply_item(self, session: Session, item: Item) -> ItemEffectResult:
        self.session = session
        self.item = item
        self.stage = BivouacStage.SETUP
        self._elapsed = 0.0
        self._duration = 1.5
        return ItemEffectResult(name=item.name, success=True)

    def update(self, session: Session, dt: float) -> None:
        session.client.push_state("SinkState")
        self._elapsed += dt

        if (
            self.stage == BivouacStage.SETUP
            and self._elapsed >= self._duration
        ):
            self.stage = BivouacStage.REST
            self._elapsed = 0.0
            self._duration = 3.0

        elif (
            self.stage == BivouacStage.REST and self._elapsed >= self._duration
        ):
            self.stage = BivouacStage.HEAL
            self._elapsed = 0.0
            session.client.event_engine.execute_action("set_monster_health")
            session.client.event_engine.execute_action("set_monster_status")
            session.client.remove_state_by_name("SinkState")
            self.stage = BivouacStage.DONE
            self._finished = True

    def is_finished(self) -> bool:
        return self._finished
