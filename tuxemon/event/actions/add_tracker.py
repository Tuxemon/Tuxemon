# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.locale import T
from tuxemon.session import Session
from tuxemon.tracker import TrackingPoint

logger = logging.getLogger(__name__)


@final
@dataclass
class AddTrackerAction(EventAction):
    """
    Add tracker.

    Script usage:
        .. code-block::

            add_tracker <character>,<location>[,visited]

    Script parameters:
        character: Either "player" or character slug name (e.g. "npc_maple").
        location: location name (e.g. "paper_town").
        visited: if it has been visited or not (true or false), default True
    """

    name = "add_tracker"
    character: str
    location: str
    visited: Optional[bool] = None

    def start(self, session: Session) -> None:
        character = get_npc(session, self.character)
        if character is None:
            logger.error(f"{self.character} not found")
            return

        if not T.has_translation("en_US", f"{self.location.lower()}"):
            logger.error(f"Add msgid '{self.location}' in the 'en_US' base.po")
            return

        visited = True if self.visited is None else self.visited
        tracking_point = TrackingPoint(visited)
        character.tracker.add_location(self.location, tracking_point)
