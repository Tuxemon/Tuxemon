# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.db import BlockedReason

if TYPE_CHECKING:
    from tuxemon.monster.monster import Monster
    from tuxemon.status.status import Status


@dataclass
class ImmunityResult:
    immune: bool
    blocked_by: str | None = None
    reason: BlockedReason | None = None


class ImmunityEngine:
    """
    Determines whether a monster is immune to a given status.
    """

    def check(self, monster: Monster, new_status: Status) -> ImmunityResult:
        item = monster.held_item
        if item and item.is_immune(new_status.slug):
            return ImmunityResult(
                immune=True,
                blocked_by=item.name,
                reason=BlockedReason.IMMUNE_BY_ITEM,
            )

        return ImmunityResult(immune=False)
