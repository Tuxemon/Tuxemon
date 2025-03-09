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

    _elements: dict[str, Element] = {}

    def __init__(self, slug: Optional[str] = None) -> None:
        self.name: str = ""
        self.icon: str = ""
        self.types: Sequence[ElementItemModel] = []

        if slug:
            self.load(slug)

    def load(self, slug: str) -> None:
        """Loads an element."""

        if slug in Element._elements:
            cached_element = Element._elements[slug]
            self.slug = slug
            self.name = cached_element.name
            self.types = cached_element.types
            self.icon = cached_element.icon
            return

        try:
            results = db.lookup(slug, table="element")
        except KeyError:
            raise RuntimeError(f"Element {slug} not found")

        self.slug = slug
        self.name = T.translate(self.slug)
        self.types = results.types
        self.icon = results.icon

        Element._elements[slug] = self

    @classmethod
    def get_element(cls, slug: str) -> Optional[Element]:
        """
        Retrieves a Element object by its slug.

        Parameters:
            slug: The unique identifier for the element.

        Returns:
            The Element object if found, otherwise None.
        """
        return cls._elements.get(slug)

    @classmethod
    def load_all_elements(cls) -> None:
        """Loads all elements from the database into the cache."""
        try:
            all_element_slugs = list(db.database["element"])
            for slug in all_element_slugs:
                cls(slug)
        except Exception as e:
            logger.error(f"Failed to load all elements: {e}")

    @classmethod
    def get_all_elements(cls) -> dict[str, Element]:
        """
        Returns all loaded elements.

        Returns:
            A dictionary of all loaded Element objects.
        """
        if not cls._elements:
            cls.load_all_elements()
        return cls._elements

    @classmethod
    def clear_cache(cls) -> None:
        """Clears the element cache."""
        cls._elements.clear()

    def __repr__(self) -> str:
        return f"Element(slug={self.slug}, name={self.name}, types={self.types}, icon={self.icon})"

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
