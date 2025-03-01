# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import Optional

from tuxemon.db import db

logger = logging.getLogger(__name__)


class Shape:
    """A shape holds all the values (speed, ranged, etc.)."""

    def __init__(self, slug: Optional[str] = None) -> None:
        self.slug = slug
        self.armour: int = 1
        self.dodge: int = 1
        self.hp: int = 1
        self.melee: int = 1
        self.ranged: int = 1
        self.speed: int = 1

        if self.slug:
            self.load(self.slug)

    def load(self, slug: str) -> None:
        """Loads shape."""

        try:
            results = db.lookup(slug, table="shape")
        except KeyError:
            raise RuntimeError(f"Shape {self.slug} not found")

        self.armour = results.armour
        self.dodge = results.dodge
        self.hp = results.hp
        self.melee = results.melee
        self.ranged = results.ranged
        self.speed = results.speed
