# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass

from tuxemon.event import MapCondition, get_npc
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session
from tuxemon.tools import compare

logger = logging.getLogger(__name__)


@dataclass
class HasItemCondition(EventCondition):
    """
    Check to see if a character inventory contains something.

    Script usage:
        .. code-block::

            is has_item <character>,<item>[,operator][,quantity]

    Script parameters:
        character: Either "player" or npc slug name (e.g. "npc_maple").
        item: The item slug name (e.g. "item_cherry").
        operator: Numeric comparison operator. Accepted values are "less_than",
            "less_or_equal", "greater_than", "greater_or_equal", "equals"
            and "not_equals".
        quantity: Quantity to compare with.

    """

    name = "has_item"

    def test(self, session: Session, condition: MapCondition) -> bool:
        def op(itm_qty: int, op: str, qty: int) -> bool:
            return compare(op, itm_qty, qty)

        npc_slug, itm_slug = condition.parameters[:2]
        npc = get_npc(session, npc_slug)
        if npc is None:
            logger.error(f"{npc_slug} doesn't exist.")
            return False
        itm = npc.find_item(itm_slug)
        if itm is None:
            return False
        else:
            if len(condition.parameters) > 2:
                operator = condition.parameters[2].lower()
                qty = int(condition.parameters[3])
                return op(itm.quantity, operator, qty)
            else:
                return True
