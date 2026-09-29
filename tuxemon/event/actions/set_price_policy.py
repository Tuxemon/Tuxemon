# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.economy.price_policy import StaticYamlPolicy, load_policy
from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class SetPricePolicyAction(EventAction):
    """
    Sets the PricePolicy for a specific NPC's economy.

    Script usage:
        .. code-block::

            set_price_policy <npc_slug>,<policy_slug>

    Script parameters:
        npc_slug: Either "player" or NPC slug (e.g. "npc_maple").
        policy_slug: Slug of a price policy (e.g. "black_market").
    """

    name = "set_price_policy"
    npc_slug: str
    policy_slug: str

    def start(self, session: Session) -> None:
        character = session.client.get_npc(self.npc_slug)
        if character is None:
            logger.error(f"{self.npc_slug} not found")
            self.stop()
            return

        if not character.economy:
            logger.error(f"NPC '{self.npc_slug}' has no economy set yet.")
            self.stop()
            return

        data = load_policy(self.policy_slug)
        if not data:
            logger.error(f"Unknown PricePolicy slug: '{self.policy_slug}'")
            self.stop()
            return

        policy = StaticYamlPolicy(data)
        character.economy.set_policy(policy)
        logger.info(
            f"Set policy '{self.policy_slug}' for NPC '{self.npc_slug}'."
        )
