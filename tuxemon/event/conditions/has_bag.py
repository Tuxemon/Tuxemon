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
class HasBagCondition(EventCondition):
    """
    Check to see how many items are in the character's bag.

    Script usage:
        .. code-block::

            is has_bag <character>,<operator>,<value>

    Script parameters:
        character: Either "player" or npc slug name (e.g. "npc_maple").
        operator: Numeric comparison operator. Accepted values are "less_than",
            "less_or_equal", "greater_than", "greater_or_equal", "equals"
            and "not_equals".
        value: The value to compare the bag with.

    """

    name = "has_bag"

    def test(self, session: Session, condition: MapCondition) -> bool:
        character_name, check, number = condition.parameters[:3]
        character = get_npc(session, character_name)
        if character is None:
            logger.error(f"Character '{character_name}' not found")
            return False

        visible_items = [
            item for item in character.items if item.behaviors.visible
        ]
        bag_size = sum(item.quantity for item in visible_items)
        return compare(check, bag_size, int(number))
