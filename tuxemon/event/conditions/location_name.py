# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass

from tuxemon.event import MapCondition
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

    name = "location_name"

    def test(self, session: Session, condition: MapCondition) -> bool:
        client = session.client
        ret: bool = False
        name = condition.parameters[0]
        names: list[str] = []
        if name.find(":") > 1:
            names = name.split(":")
        else:
            names.append(name)

        if client.map_slug in names:
            ret = True
        return ret
