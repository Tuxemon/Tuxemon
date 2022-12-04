from __future__ import annotations

from dataclasses import dataclass

from tuxemon.db import MapType
from tuxemon.item.itemcondition import ItemCondition
from tuxemon.monster import Monster


@dataclass
class LocationTypeCondition(ItemCondition):
    """
    Checks against the location type the player's in.

    Shop, center, town, route, dungeon or notype.

    """

    name = "location_type"
    location_type: str

    def test(self, target: Monster) -> bool:
        types = [maps.value for maps in MapType]
        if self.location_type in types:
            if self.session.client.map_type == self.location_type:
                return True
            else:
                return False
        else:
            return False
