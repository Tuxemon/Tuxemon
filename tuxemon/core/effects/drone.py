# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, ItemEffectResult
from tuxemon.platform.const.sizes import KENNEL

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session


class DroneStage(Enum):
    LAUNCH = 1
    TRAVEL = 2
    ARRIVAL = 3
    SWAP = 4
    RETURN = 5
    DONE = 6


@dataclass
class DroneEffect(CoreEffect):
    """
    Swaps a monster from the player's party with one from the specified
    monster box (``KENNEL``).

    This effect simulates a drone sequence with multiple stages (launch,
    travel, arrival, swap, return, done). The player selects a party monster
    to be swapped with a monster from the box. If no monsters are available
    in the box, the effect fails.

    **Parameters**

    - ``stage``: The current stage of the drone sequence (default: ``LAUNCH``).
    - ``_elapsed``: Internal timer tracking elapsed time in the current stage.
    - ``_duration``: Duration of the current stage.
    - ``_finished``: Whether the drone sequence has completed.

    **Example**

    .. code-block:: json

        "effects": [
            "drone"
        ]
    """

    name = "drone"
    stage: DroneStage = DroneStage.LAUNCH
    _elapsed: float = 0.0
    _duration: float = 0.0
    _finished: bool = False

    def apply_item(self, session: Session, item: Item) -> ItemEffectResult:
        self.session = session
        self.item = item
        self.stage = DroneStage.LAUNCH
        self._elapsed = 0.0
        self._duration = 1.0
        return ItemEffectResult(name=item.name, success=True)

    def update(self, session: Session, dt: float) -> None:
        session.client.push_state("SinkState")
        if self.stage == DroneStage.DONE:
            return

        self._elapsed += dt

        if self.stage == DroneStage.LAUNCH and self._elapsed >= self._duration:
            self.stage = DroneStage.TRAVEL
            self._elapsed = 0.0
            self._duration = 2.0

        elif (
            self.stage == DroneStage.TRAVEL and self._elapsed >= self._duration
        ):
            self.stage = DroneStage.ARRIVAL
            self._elapsed = 0.0
            self._duration = 0.5

        elif (
            self.stage == DroneStage.ARRIVAL
            and self._elapsed >= self._duration
        ):
            size = session.player.monster_boxes.get_box_size(KENNEL, "monster")
            if size == 0:
                self._finished = True
                self.stage = DroneStage.DONE
                return

            def on_party_monster_selected(monster: Monster) -> None:
                session.client.push_state(
                    "MonsterTakeState",
                    box_name=KENNEL,
                    character=session.player,
                    swap_target=monster,
                )
                self.stage = DroneStage.RETURN
                self._elapsed = 0.0
                self._duration = 1.5

            session.client.push_state(
                "MonsterDropOff",
                box_name=KENNEL,
                character=session.player,
                on_selection=on_party_monster_selected,
            )
            self.stage = DroneStage.SWAP
            self._elapsed = 0.0
            self._duration = 0.0  # waiting for user input

        elif (
            self.stage == DroneStage.RETURN and self._elapsed >= self._duration
        ):
            session.client.remove_state_by_name("SinkState")
            self.stage = DroneStage.DONE
            self._finished = True

    def is_finished(self) -> bool:
        return self._finished
