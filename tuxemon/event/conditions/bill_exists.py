# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import ClassVar

from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@dataclass
class BillExistsCondition(EventCondition):
    """
    Check to see if a bill exists.

    Script usage:
        .. code-block::

            is bill_exists <character>,<bill_slug>

    Script parameters:
        character: Either "player" or npc slug name (e.g. "npc_maple").
        bill_slug: The slug of the bill

    eg. "is bill_exists player,my_bill"
    """

    name: ClassVar[str] = "bill_exists"
    character: str
    bill_slug: str

    def test(self, session: Session) -> bool:
        character = session.client.get_npc(self.character)
        if character is None:
            logger.error(f"Character '{self.character}' not found")
            return False

        money_manager = character.money_controller.money_manager
        bill = money_manager.get_bill(self.bill_slug)
        return bill is not None
