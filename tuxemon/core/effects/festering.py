# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, StatusEffectResult

if TYPE_CHECKING:
    from tuxemon.session import Session
    from tuxemon.status.status import Status


@dataclass
class FesteringEffect(CoreEffect):
    """
    Applies the "festering" status to a monster.

    This effect represents a lingering condition that can be applied during
    combat. Once triggered, the status is considered active and reported as
    successful.

    **Example**

    .. code-block:: json

        "effects": [
            "festering"
        ]
    """

    name = "festering"

    def apply_status(
        self, session: Session, status: Status
    ) -> StatusEffectResult:
        return StatusEffectResult(name=status.name, success=True)
