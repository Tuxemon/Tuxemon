# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import ClassVar

from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session
from tuxemon.tools import compare

logger = logging.getLogger(__name__)


@dataclass
class HasKennelCondition(EventCondition):
    """
    Check to see how many monsters are in the character's kennel.

    Script usage:
        .. code-block::

            is has_kennel <character>,<kennel>,<operator>,<value>

    Script parameters:
        character: Either "player" or npc slug name (e.g. "npc_maple").
        kennel: The kennel name.
        operator: Numeric comparison operator. Accepted values are "less_than",
            "less_or_equal", "greater_than", "greater_or_equal", "equals"
            and "not_equals".
        value: The value to compare the party with.
    """

    name: ClassVar[str] = "has_kennel"
    character: str
    kennel: str
    operator: str
    value: int

    def test(self, session: Session) -> bool:
        character = session.client.get_npc(self.character)
        if character is None:
            logger.error(f"{self.character} not found")
            return False
        if not character.monster_boxes.has_box(self.kennel, "monster"):
            raise ValueError(f"{self.kennel} doesn't exist.")
        party_size = character.monster_boxes.get_box_size(
            self.kennel, "monster"
        )
        return compare(self.operator, party_size, self.value)
