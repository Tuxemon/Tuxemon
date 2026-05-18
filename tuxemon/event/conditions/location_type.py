# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from tuxemon.event.eventcondition import EventCondition
from tuxemon.map.manager import MAP_TYPES
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

    name: ClassVar[str] = "location_type"
    location: str

    def test(self, session: Session) -> bool:
        client = session.client
        locs = (
            self.location.split(":")
            if ":" in self.location
            else (
                list(MAP_TYPES.keys())
                if self.location == "all"
                else [self.location]
            )
        )

        return client.map_manager.map_type.name in locs
