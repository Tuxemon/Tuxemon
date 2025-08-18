# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass

from tuxemon.event import MapCondition, get_npc
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

    name = "bill_exists"

    def test(self, session: Session, condition: MapCondition) -> bool:
        character_name, bill_slug = condition.parameters[:2]
        character = get_npc(session, character_name)
        if character is None:
            logger.error(f"Character '{character_name}' not found")
            return False

        money_manager = character.money_controller.money_manager
        bill = money_manager.get_bill(bill_slug)
        return bill is not None
