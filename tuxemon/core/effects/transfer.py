# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session
    from tuxemon.technique.technique import Technique


@dataclass
class TransferEffect(CoreEffect):
    """
    Applies the "transfer" effect to a technique.

    This effect moves a specified condition (status) from one entity to
    another. The direction of transfer is controlled by the ``direction``
    attribute, which determines whether the condition is passed from the
    user to the target or vice versa. Once transferred, the condition is
    removed from the source entity.

    **Parameters**

    - ``condition``: String name of the condition to transfer.
    - ``direction``: String specifying the transfer direction.
      - ``user_to_target`` → transfers condition from the user to the target.
      - ``target_to_user`` → transfers condition from the target to the user.

    **Example**

    .. code-block:: json

        "effects": [
            "transfer poison user_to_target"
        ]

        "effects": [
            "transfer burn target_to_user"
        ]
    """

    name = "transfer"
    condition: str
    direction: str

    def apply_tech_target(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> TechEffectResult:
        hit = session.client.combat_session.get_tech_hit(user)
        tech.hit = tech.accuracy >= hit
        done = False
        if tech.hit:
            source, dest = (
                (user, target)
                if self.direction == "user_to_target"
                else (target, user)
            )
            if source.status.has_status(self.condition):
                dest.status = source.status
                source.status.clear_status(session)
                done = True
        return TechEffectResult(name=tech.name, success=done)
