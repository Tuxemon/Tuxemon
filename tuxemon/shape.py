# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import Union

from tuxemon.db import MonsterShape, db

logger = logging.getLogger(__name__)


class Shape:
    """A shape holds all the values (speed, ranged, etc.)."""

    def __init__(self, slug: Union[str, None] = None) -> None:
        self.slug = MonsterShape.landrace
        self.armour: int = 1
        self.dodge: int = 1
        self.hp: int = 1
        self.melee: int = 1
        self.ranged: int = 1
        self.speed: int = 1
        if slug:
            if slug == MonsterShape.default:
                pass
            else:
                self.load(slug)

    def load(self, slug: str) -> None:
        """Loads shape."""

        if slug == MonsterShape.default:
            pass
        else:
            results = db.lookup(slug, table="shape")

        self.slug = results.slug or self.slug
        self.armour = results.armour or self.armour
        self.dodge = results.dodge or self.dodge
        self.hp = results.hp or self.hp
        self.melee = results.melee or self.melee
        self.ranged = results.ranged or self.ranged
        self.speed = results.speed or self.speed
