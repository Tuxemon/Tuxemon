#
# Tuxemon
# Copyright (c) 2014-2017 William Edwards <shadowapex@gmail.com>,
#                         Benjamin Bean <superman2k5@gmail.com>
#
# This file is part of Tuxemon
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

from operator import eq, gt, lt, ge, le

from tuxemon.event import get_npc, MapCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session
from typing import Optional, Mapping, Callable

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

            is has_item <character> <item> [operator] [quantity]

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
