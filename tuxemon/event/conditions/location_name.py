# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session


@dataclass
class LocationNameCondition(EventCondition):
    """
    Check to see if the player is in a certain location name.

    Script usage:
        .. code-block::

            is location_name <slug>

    Script parameters:
        slug: Slug name. It's the name inside the maps.
        eg. "<property name="slug" value="routeb"/>"
        slug = routeb

    eg. "is location_name routeb"
    eg. "is location_name routeb:routea"
    """

    name: ClassVar[str] = "location_name"
    location: str

    def test(self, session: Session) -> bool:
        client = session.client
        slugs = [s for s in self.location.split(":") if s]
        return client.map_manager.map_slug in slugs
