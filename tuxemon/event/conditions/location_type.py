# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass

from tuxemon.event import MapCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.map_manager import map_types_list
from tuxemon.session import Session


@dataclass
class LocationTypeCondition(EventCondition):
    """
    Determines whether the player is currently in a specified location type.

    Script usage:
        .. code-block::

            is location_type <slug>

    Script parameters:
        slug: A string identifier for the location type.
        Acceptable values: "all" (matches any location)

    Example usages:
        - "is location_type clinic"  -> Checks if the player is in a clinic.
        - "is location_type town:shop"  -> Checks if the player is in either
            a town or a shop.

    The condition evaluates whether the player's current map type matches
    any of the specified location types.
    """

    name = "location_type"

    def test(self, session: Session, condition: MapCondition) -> bool:
        client = session.client
        location = condition.parameters[0]

        locs = (
            location.split(":")
            if ":" in location
            else (map_types_list if location == "all" else [location])
        )

        return client.map_manager.map_type.name in locs
