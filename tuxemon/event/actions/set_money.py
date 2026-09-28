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
class SetMoneyAction(EventAction):
    """
    Set an amount of money for a specific slug.

    Script usage:
        .. code-block::

            set_money <slug>,[amount]

    Script parameters:
        character: Either "player" or character slug name (e.g. "npc_maple").
        amount: Amount of money (>= 0) (default 0)
    """

    name = "set_money"
    character: str
    amount: int | None = None

    def start(self, session: Session) -> None:
        character = session.client.get_npc(self.character)

        if character is None:
            logger.error(f"Character '{self.character}' not found")
            self.stop()
            return

        amount = 0 if self.amount is None else self.amount
        money_manager = character.money_controller.money_manager
        money_manager.set_money(amount)
        logger.debug(f"{character.name}'s money set to {amount}")
