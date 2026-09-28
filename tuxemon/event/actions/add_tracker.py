# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, final

from tuxemon.event.eventaction import EventAction
from tuxemon.locale.locale import T
from tuxemon.tools import parse_flag
from tuxemon.tracker import TrackingPoint

if TYPE_CHECKING:
    from tuxemon.session import Session

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
        visited: Optional string flag indicating if the location was visited.
            Accepts "true", "1", "yes" for True (case-insensitive).
            Defaults to True if omitted.
    """

    name = "add_tracker"
    character: str
    location: str
    visited: str | None = None

    def start(self, session: Session) -> None:
        character = session.client.get_npc(self.character)
        if character is None:
            logger.error(f"{self.character} not found")
            self.stop()
            return

        if not T.has_translation("en_US", f"{self.location.lower()}"):
            logger.error(f"Add msgid '{self.location}' in the 'en_US' base.po")
            self.stop()
            return

        visited = True if self.visited is None else parse_flag(self.visited)
        tracking_point = TrackingPoint(visited)
        character.tracker.add_location(self.location, tracking_point)
