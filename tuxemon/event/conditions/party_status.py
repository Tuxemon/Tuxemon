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
class PartyStatusCondition(EventCondition):
    """
    Check how many monsters in a character's party have a specific status.

    Script usage:
        .. code-block::

            is party_status <character>,<operator>,<value>,<status_name>

    Script parameters:
        character: Either "player" or npc slug name (e.g. "npc_maple").
        operator: Numeric comparison operator. Accepted values are "less_than",
            "less_or_equal", "greater_than", "greater_or_equal", "equals"
            and "not_equals".
        value: Integer to compare against.
        status_name: Slug of the status to check (e.g. "poison").
    """

    name: ClassVar[str] = "party_status"
    character: str
    operator: str
    value: int
    status: str

    def test(self, session: Session) -> bool:
        character = session.client.get_npc(self.character)
        if character is None:
            logger.error(f"{self.character} not found")
            return False

        count = sum(
            1
            for m in character.monsters
            if (current_status := m.status.current_status) is not None
            and current_status.slug == self.status
        )
        return compare(self.operator, count, self.value)
