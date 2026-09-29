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
class TrackerCondition(EventCondition):
    """
    Check to see if tracker exists.

    Script usage:
        .. code-block::

            is tracker character,map_name

    Script parameters:
        character: Either "player" or npc slug name (e.g. "npc_maple").
        map_name: The name of the map to validate against.
    """

    name: ClassVar[str] = "tracker"
    character: str
    map_name: str

    def test(self, session: Session) -> bool:
        character = session.client.get_npc(self.character)
        if character is None:
            logger.error(f"{self.character} not found")
            return False

        return character.tracker.get_location(self.map_name) is not None
