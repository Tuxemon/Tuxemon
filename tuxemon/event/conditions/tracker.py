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

    name = "tracker"

    def test(self, session: Session, condition: MapCondition) -> bool:
        _character, _map_name = condition.parameters
        character = get_npc(session, _character)
        if character is None:
            logger.error(f"{_character} not found")
            return False

        return character.tracker.get_location(_map_name) is not None
