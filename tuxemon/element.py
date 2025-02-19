# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Optional

from tuxemon.db import ElementItemModel, db
from tuxemon.locale import T

logger = logging.getLogger(__name__)


class Element:
    """An Element holds a list of types and multipliers."""

    def __init__(self, slug: Optional[str] = None) -> None:
        self.name: str = ""
        self.icon: str = ""
        self.types: Sequence[ElementItemModel] = []

        if slug:
            self.load(slug)

    def load(self, slug: str) -> None:
        """Loads an element."""
        try:
            results = db.lookup(slug, table="element")
        except KeyError:
            raise RuntimeError(f"Element {slug} not found")

        self.slug = slug
        self.name = T.translate(self.slug)
        self.types = results.types
        self.icon = results.icon

    def lookup_field(self, element: str, field: str) -> Optional[float]:
        """Looks up the element against for this element."""
        for item in self.types:
            if item.against == element and hasattr(item, field):
                return float(getattr(item, field))
        return None

    def lookup_multiplier(self, element: str) -> float:
        """Looks up the element multiplier for this element."""
        mult = self.lookup_field(element, "multiplier")
        if mult is None:
            logger.error(
                f"Multiplier for element '{element}' not found in "
                f"this element '{self.slug}'"
            )
            return 1.0
        return mult
