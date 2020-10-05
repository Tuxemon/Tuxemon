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

from tuxemon.core.event import get_npc
from tuxemon.core.event.eventcondition import EventCondition

cmp_dict = {
    None: ge,
    "less_than": lt,
    "less_or_equal": le,
    "greater_than": gt,
    "greater_or_equal": ge,
    "equals": eq
}


class HasItemCondition(EventCondition):
    """ Checks to see if a NPC inventory contains something

    inventory_contains [npc_slug or player] [item slug] [operator] [quantity]

    npc or player: "player" or npc slug name; "npc_maple"
    item slug: the item slug name; item_cherry, etc
    operator: numeric comparison operators: less_than, greater_than, equals, less_or_equal, greater_or_equal
    quantity: integer value, non-negative

    operator can be optional; it will default to greater_or_equal
    quantity can be optional; it will default to 1

    if quantity is None, then any number of items over 0 will return True ( quantity >= 1 )
    """
    name = "has_item"

    def test(self, session,  condition):
        """ Checks to see the player is has a monster in his party

        :type session: tuxemon.core.session.Session
        :type condition: Dictionary

        :rtype: Boolean
        """
        try:
            raw_op = condition.parameters[2].lower()
            if raw_op == '':
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
        item_info = npc.inventory.get(item_slug)
        if item_info is None:  # not found in inventory
            item_quantity = 0
        else:
            item_quantity = item_info['quantity']

        return op(item_quantity, q_test)
