# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import Any, List, Mapping, Optional, Sequence

from tuxemon.db import db

logger = logging.getLogger(__name__)

SIMPLE_PERSISTANCE_ATTRIBUTES = (
    "slug",
    "sprite_name",
    "combat_front",
)


class Template:
    """
    Tuxemon template.

    """

    def __init__(self, save_data: Optional[Mapping[str, Any]] = None) -> None:
        if save_data is None:
            save_data = dict()

        self.slug: str = ""
        self.sprite_name: str = ""
        self.combat_front: str = ""
        self.double: bool = False

        self.set_state(save_data)

    def load(self, slug: str) -> None:
        """
        Loads and sets template from the db.

        """
        results = db.lookup(slug, table="template")

        if results is None:
            raise RuntimeError(f"template {slug} is not found")

        self.slug = results.slug
        self.double = results.double

    def get_state(self) -> Mapping[str, Any]:
        """
        Prepares a dictionary of the template to be saved to a file.

        """
        save_data = {
            attr: getattr(self, attr)
            for attr in SIMPLE_PERSISTANCE_ATTRIBUTES
            if getattr(self, attr)
        }

        return save_data

    def set_state(self, save_data: Mapping[str, Any]) -> None:
        """
        Loads information from saved data.

        """
        if not save_data:
            return

        self.load(save_data["slug"])

        for key, value in save_data.items():
            if key in SIMPLE_PERSISTANCE_ATTRIBUTES:
                setattr(self, key, value)


def decode_template(
    json_data: Optional[Sequence[Mapping[str, Any]]],
) -> List[Template]:
    return [Template(save_data=tmp) for tmp in json_data or {}]


def encode_template(tmps: Sequence[Template]) -> Sequence[Mapping[str, Any]]:
    return [tmp.get_state() for tmp in tmps]
