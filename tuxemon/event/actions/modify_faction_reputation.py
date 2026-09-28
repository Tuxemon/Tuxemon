# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class ModifyFactionReputationAction(EventAction):
    """
    Modifies an NPC's (or player's) reputation with a specific faction.

    Script usage:
        .. code-block::

            modify_faction_reputation <character>,<faction_slug>,<amount>

    Script parameters:
        character: Either "player" or npc slug name (e.g. "npc_maple").
        faction_slug: The slug identifier of the faction to modify reputation for.
        amount: A string representation of an integer. Positive or negative values
            (e.g. "25", "-50") that change the reputation score accordingly.
    """

    name = "modify_faction_reputation"
    character: str
    faction_slug: str
    amount: int

    def start(self, session: Session) -> None:
        char = session.client.get_npc(self.character)
        if not char:
            logger.error(f"[Reputation] NPC '{self.character}' not found.")
            self.stop()
            return

        faction_manager = session.world.faction_manager
        faction = faction_manager.get(self.faction_slug)
        if not faction:
            logger.error(
                f"[Reputation] Faction '{self.faction_slug}' not found."
            )
            self.stop()
            return

        faction.modify_reputation(char.slug, self.amount)
        logger.info(
            f"[Reputation] {char.slug}'s rep in {self.faction_slug} changed by {self.amount}. "
            f"New rep: {faction.get_reputation(char.slug)}"
        )
        faction.evaluate_rank_change(char.slug, char.variable_manager)
        faction_manager.clear_membership_cache(char.slug)
