# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from operator import eq, ge, gt, le, lt

from tuxemon.event import MapCondition, get_npc
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session


class HasItemCondition(EventCondition):
    """
    Check to see if a NPC inventory contains something.

    Script usage:
        .. code-block::

            is has_item <character>,<item>[,operator][,quantity]

    Script parameters:
        character: Either "player" or npc slug name (e.g. "npc_maple").
        item: The item slug name (e.g. "item_cherry").
        operator: Numeric comparison operator. Accepted values are "less_than",
            "greater_than", "equals", "less_or_equal" and "greater_or_equal".
        quantity: Quantity to compare with.

    """

    name = "has_item"

    def test(self, session: Session, condition: MapCondition) -> bool:
        """
        Check to see a character has a particular number of items.

        Parameters:
            session: The session object
            condition: The map condition object.

        Returns:
            Whether the target character has the desired quantity of a
            the specified item.

        """

        def op(itm_qty: int, op: str, qty: int) -> bool:
            if op == "less_than":
                return bool(lt(itm_qty, qty))
            elif op == "less_or_equal":
                return bool(le(itm_qty, qty))
            elif op == "greater_than":
                return bool(gt(itm_qty, qty))
            elif op == "greater_or_equal":
                return bool(ge(itm_qty, qty))
            else:
                return bool(eq(itm_qty, qty))

        npc_slug, itm_slug = condition.parameters[:2]
        npc = get_npc(session, npc_slug)
        if npc is not None:
            assert npc
            itm = npc.find_item(itm_slug)
            if itm is None:
                return False
            else:
                if len(condition.parameters) > 2:
                    operator = condition.parameters[2].lower()
                    qty = int(condition.parameters[3])
                    return op(itm.quantity, operator, qty)
                else:
                    return False
        else:
            raise ValueError(f"{npc_slug} doesn't exist.")
