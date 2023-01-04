# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from operator import eq, ge, gt, le, lt
from typing import Callable, Mapping, Optional

from tuxemon.event import MapCondition, get_npc
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session

cmp_dict: Mapping[Optional[str], Callable[[object, object], bool]] = {
    None: ge,
    "less_than": lt,
    "less_or_equal": le,
    "greater_than": gt,
    "greater_or_equal": ge,
    "equals": eq,
}


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
            The default value is "greater_or_equal".
        quantity: Quantity to compare with. Must be a non-negative integer. The
            default value is 1.

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
        try:
            raw_op: Optional[str] = condition.parameters[2].lower()
            if raw_op == "":
                raw_op = None
        except (IndexError, AttributeError):
            raw_op = None

        try:
            op = cmp_dict[raw_op]
        except KeyError:
            raise ValueError

        try:
            q_test = int(condition.parameters[3])
            if q_test < 0:
                raise ValueError
        except IndexError:
            q_test = 1

        # TODO: handle missing npc, etc
        owner_slug, item_slug = condition.parameters[:2]
        npc = get_npc(session, owner_slug)
        assert npc
        item_info = npc.inventory.get(item_slug)
        if item_info is None:  # not found in inventory
            item_quantity = 0
        else:
            item_quantity = item_info["quantity"]

        return op(item_quantity, q_test)
