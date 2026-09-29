# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.economy.applier import EconomyApplier
from tuxemon.economy.economy import Economy
from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class SetEconomyAction(EventAction):
    """
    Sets the economy (prices and initial stock of items/monsters) for a specific NPC.

    This action orchestrates loading the economy data and then applying it to
    the target character's shop/inventory, including handling initial quantities
    and variable-based availability.

    Script usage:
        .. code-block::

            set_economy <npc_slug>,<economy_slug>

    Script parameters:
        npc_slug: Either "player" or npc slug name (e.g. "npc_maple").
        economy_slug: Slug of an economy.
    """

    name = "set_economy"
    npc_slug: str
    economy_slug: str

    def start(self, session: Session) -> None:
        character = session.client.get_npc(self.npc_slug)
        if character is None:
            logger.error(f"{self.npc_slug} not found")
            self.stop()
            return

        try:
            character.economy = Economy(self.economy_slug)
            logger.info(
                f"Loaded economy '{self.economy_slug}' for NPC '{self.npc_slug}'."
            )
        except RuntimeError as e:
            logger.error(f"Error loading economy '{self.economy_slug}': {e}")
            self.stop()
            return

        applier = EconomyApplier()
        applier.apply_economy_to_character(
            session,
            character.economy,
            character,
            session.client.shop_manager,
        )
