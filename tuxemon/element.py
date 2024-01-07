# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import Union

from tuxemon.db import ElementType, db

logger = logging.getLogger(__name__)


class Element:
    """An Element holds a list of types and multipliers."""

    def __init__(self, slug: Union[str, None] = None) -> None:
        self.name: str = ""
        self.icon: str = ""
        if slug:
            self.load(slug)

    def load(self, slug: str) -> None:
        """Loads an element."""
        results = db.lookup(slug, table="element")
        if results is None:
            raise RuntimeError(f"element {slug} is not found")
        self.slug = results.slug
        self.name = results.slug.name
        self.types = results.types
        self.icon = results.icon

    def lookup_field(
        self, element: ElementType, field: str
    ) -> Union[float, None]:
        """Looks up the element against for this element."""
        for item in self.types:
            if item.against == element and hasattr(item, field):
                value = float(getattr(item, field))
                return value
        return None

    def lookup_multiplier(self, element: ElementType) -> float:
        """Looks up the element multiplier for this element."""
        mult = self.lookup_field(element, "multiplier")

        if mult is None:
            mult = 1.0
            logger.error(
                f"Multiplier for element '{element}' not found in "
                f"this element '{self.slug}'"
            )
        return mult
