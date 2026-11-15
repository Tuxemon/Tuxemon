# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.constants.asset_loader import fetch_asset
from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class ManageMapCacheAction(EventAction):
    """
    Adds or removes a map from the cache.

    Script usage:
        .. code-block::

            manage_map_cache <action>,<map_name>

    Script parameters:
        action: "add" or "remove"
        map_name: Name of the map (map.tmx)
    """

    name = "manage_map_cache"
    action: str
    map_name: str

    def start(self, session: Session) -> None:
        target_map = fetch_asset("maps", self.map_name)

        if self.action == "add":
            try:
                map_data = session.client.map_loader.load_map_data(target_map)
                session.client.map_loader.add_to_cache(target_map, map_data)
                logger.info(f"Map '{target_map}' manually added to cache.")
            except Exception as e:
                logger.error(f"Failed to load map '{target_map}': {e}")

        elif self.action == "remove":
            removed = session.client.map_loader.remove_from_cache(target_map)
            if removed:
                logger.info(f"Map '{target_map}' removed from cache.")
            else:
                logger.warning(f"Map '{target_map}' not found in cache.")

        else:
            logger.error(f"Unknown cache action: '{self.action}'")
