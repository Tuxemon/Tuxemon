# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class TrackingPoint:
    visited: bool = True

    def get_state(self) -> dict[str, Any]:
        return {
            "visited": self.visited,
        }


class TrackingData:
    def __init__(self) -> None:
        self.locations: dict[str, TrackingPoint] = {}

    def add_location(self, location_id: str, location: TrackingPoint) -> None:
        if location_id in self.locations:
            logger.error(f"TrackingPoint ID '{location_id}' already exists.")
        else:
            self.locations[location_id] = location

    def remove_location(self, location_id: str) -> None:
        if location_id in self.locations:
            del self.locations[location_id]
            logger.info(f"TrackingPoint ID '{location_id}' has been removed.")
        else:
            logger.error(f"TrackingPoint ID '{location_id}' does not exist.")

    def get_location(self, location_id: str) -> Optional[TrackingPoint]:
        if location_id in self.locations:
            return self.locations[location_id]
        else:
            return None


def decode_tracking(json_data: Mapping[str, Any]) -> TrackingData:
    tracking_data = TrackingData()
    if json_data:
        tracking_data.locations = {
            key: TrackingPoint(**value) for key, value in json_data.items()
        }
    else:
        tracking_data.locations = {}
    return tracking_data


def encode_tracking(tracking_data: TrackingData) -> Mapping[str, Any]:
    return {
        "tracker": {
            location: data.get_state()
            for location, data in tracking_data.locations.items()
        }
    }
