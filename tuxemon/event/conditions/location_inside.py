# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from tuxemon.event import MapCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session


class LocationInsideCondition(EventCondition):
    """
    Check to see if the player is in a certain location type.

    Script usage:
        .. code-block::

            is location_inside

    eg. "is location_inside"

    """

    name = "location_inside"

    def test(self, session: Session, condition: MapCondition) -> bool:
        client = session.client
        return client.map_inside
