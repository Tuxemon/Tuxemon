# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction

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
    amount: Optional[int] = None

    def start(self) -> None:
        character = get_npc(self.session, self.character)

        if character is None:
            logger.error(f"Character '{self.character}' not found")
            return

        amount = 0 if self.amount is None else self.amount
        if amount < 0:
            raise AttributeError(f"{amount} must be >= 0")
        else:
            money_manager = character.money_controller.money_manager
            money_manager.add_money(amount)
            logger.info(f"{character.name}'s have {amount}")
