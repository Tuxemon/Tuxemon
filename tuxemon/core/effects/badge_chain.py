# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session


@dataclass
class BadgeChainEffect(CoreEffect):
    """Mints a SolaMon Badges NFT for the current player.

    Example: ``badge_chain first_gym``
    """

    name = "badge_chain"
    badge_id: str

    def apply(
        self, session: Session, user: Monster, target: Monster
    ) -> TechEffectResult:
        if session._client is not None:
            session.client.solana_manager.mint_badge(self.badge_id)
        return TechEffectResult(name=self.badge_id, success=True)
