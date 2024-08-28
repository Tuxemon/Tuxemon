# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import uuid
from collections.abc import Mapping, Sequence
from typing import Any, Optional

from tuxemon.db import MissionStatus, db
from tuxemon.locale import T

SIMPLE_PERSISTANCE_ATTRIBUTES = (
    "slug",
    "status",
)


class Mission:
    """
    Tuxemon mission.

    """

    def __init__(self, save_data: Optional[Mapping[str, Any]] = None) -> None:
        save_data = save_data or {}

        self.slug: str = ""
        self.name: str = ""
        self.description: str = ""
        self.status: MissionStatus = MissionStatus.pending

        self.set_state(save_data)

    def load(self, slug: str) -> None:
        """
        Loads and sets mission from the db.

        """
        try:
            results = db.lookup(slug, table="mission")
        except KeyError:
            raise RuntimeError(f"Mission {slug} not found")

        self.instance_id = uuid.uuid4()
        self.slug = results.slug
        self.name = T.translate(results.slug)
        self.status = self.status

    def get_state(self) -> Mapping[str, Any]:
        """
        Prepares a dictionary of the mission to be saved to a file.

        """
        save_data = {
            attr: getattr(self, attr)
            for attr in SIMPLE_PERSISTANCE_ATTRIBUTES
            if getattr(self, attr)
        }

        save_data["instance_id"] = str(self.instance_id.hex)

        return save_data

    def set_state(self, save_data: Mapping[str, Any]) -> None:
        """
        Loads information from saved data.

        """
        if not save_data:
            return

        self.load(save_data["slug"])

        for key, value in save_data.items():
            if key == "instance_id" and value:
                self.instance_id = uuid.UUID(value)
            elif key in SIMPLE_PERSISTANCE_ATTRIBUTES:
                setattr(self, key, value)


def decode_mission(
    json_data: Optional[Sequence[Mapping[str, Any]]],
) -> list[Mission]:
    return [Mission(save_data=mission) for mission in json_data or {}]


def encode_mission(missions: Sequence[Mission]) -> Sequence[Mapping[str, Any]]:
    return [mission.get_state() for mission in missions]
