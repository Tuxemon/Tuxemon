# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Optional

from tuxemon.db import ElementItemModel, ElementModel, db
from tuxemon.locale import T

logger = logging.getLogger(__name__)


class Element:
    """An Element holds a list of types and multipliers."""

    _elements: dict[str, Element] = {}

    def __init__(self, slug: Optional[str] = None) -> None:
        self.slug: str = ""
        self.icon: str = ""
        self.types: Sequence[ElementItemModel] = []

        if slug:
            self.load(slug)

    def load(self, slug: str) -> None:
        """Loads an element."""

        if slug in Element._elements:
            cached_element = Element._elements[slug]
            self.slug = slug
            self.types = cached_element.types
            self.icon = cached_element.icon
            return

        results = ElementModel.lookup(slug, db)
        self.slug = slug
        self.types = results.types
        self.icon = results.icon

        Element._elements[slug] = self

    @property
    def name(self) -> str:
        """Translated display name for this element."""
        return T.translate(self.slug) if self.slug else ""

    @classmethod
    def get_element(cls, slug: str) -> Optional[Element]:
        """Retrieves an Element object by its slug."""
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
        """Returns all loaded elements."""
        if not cls._elements:
            cls.load_all_elements()
        return cls._elements

    @classmethod
    def clear_cache(cls) -> None:
        """Clears the element cache."""
        cls._elements.clear()

    def __repr__(self) -> str:
        return (
            f"Element(slug={self.slug}, "
            f"name={self.name}, "
            f"types={self.types}, "
            f"icon={self.icon}, "
        )

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
                f"Multiplier for element '{element}' not found in this element '{self.slug}'"
            )
            return 1.0
        return mult


class ElementTypesHandler:

    def __init__(self, initial_types: Optional[Sequence[str]] = None):
        pre_types = (
            []
            if initial_types is None
            else [Element(ele) for ele in initial_types]
        )
        self._current_types = pre_types
        self._default_types = list(pre_types)

    def set_types(self, new_types: list[Element]) -> None:
        self._current_types = new_types

    def reset_to_default(self) -> None:
        self._current_types = list(self._default_types)

    def get_type_slugs(self) -> list[str]:
        return [element.slug for element in self._current_types]

    def has_type(self, type_slug: str) -> bool:
        return type_slug in {type_obj.slug for type_obj in self._current_types}

    @property
    def current(self) -> list[Element]:
        return list(self._current_types)

    @property
    def default(self) -> list[Element]:
        return list(self._default_types)

    @property
    def primary(self) -> Element:
        if not self._current_types:
            raise ValueError(
                "No types available, cannot determine primary type."
            )
        return self._current_types[0]
