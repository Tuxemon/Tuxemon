# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Sequence

from tuxemon.database.runtime import db
from tuxemon.db import ElementItemModel, ElementModel
from tuxemon.locale.locale import T

logger = logging.getLogger(__name__)


class Element:
    """An Element holds a list of types and multipliers."""

    _elements: dict[str, Element] = {}

    def __init__(
        self,
        slug: str,
        icon: str,
        types: Sequence[ElementItemModel],
    ) -> None:
        self.slug = slug
        self.icon = icon
        self.types = list(types)

    @property
    def name(self) -> str:
        """Translated display name for this element."""
        return T.translate(self.slug) if self.slug else ""

    @classmethod
    def get(cls, slug: str) -> Element:
        """
        Retrieve an Element from cache or load it from the database.
        """
        if slug in cls._elements:
            return cls._elements[slug]

        try:
            results = ElementModel.lookup(slug, db)
            icon = results.icon
            types = results.types
        except Exception:
            logger.warning(f"Element {slug} not found, using empty fallback.")
            icon = ""
            types = []

        element = cls(slug, icon, types)
        cls._elements[slug] = element
        return element

    @classmethod
    def load_all_elements(cls) -> None:
        """Loads all elements from the database into the cache."""
        try:
            for slug in db.database["element"]:
                cls.get(slug)
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
            f"icon={self.icon})"
        )

    def lookup_field(self, element: str, field: str) -> float | None:
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
    """
    Handles element type sets and affinity/resistance calculations.
    Uses Element templates via Element.get and caches multipliers.
    """

    _multiplier_cache: dict[tuple[str, str], float] = {}

    def __init__(self, initial_types: Sequence[str] | None = None):
        if initial_types is None:
            pre_types: list[Element] = []
        else:
            pre_types = [Element.get(slug) for slug in initial_types]

        self._current_types: list[Element] = pre_types
        self._default_types: list[Element] = list(pre_types)

    @classmethod
    def calculate_affinity_score(
        cls, user_types: Sequence[Element], target_types: Sequence[Element]
    ) -> float:
        """
        Return cumulative offensive multiplier of user types against target types.
        """
        multiplier = 1.0
        for _user in user_types:
            for _target in target_types:
                if _target:
                    key = (_user.slug, _target.slug)
                    if key not in cls._multiplier_cache:
                        cls._multiplier_cache[key] = _user.lookup_multiplier(
                            _target.slug
                        )
                    mult_value = cls._multiplier_cache[key]
                    multiplier *= mult_value
        return multiplier

    @classmethod
    def calculate_resistance_multiplier_for_types(
        cls, defending_types: Sequence[Element], attacking_slug: str
    ) -> float:
        """
        Return cumulative defensive multiplier of defending types against an
        attacking type.
        """
        multiplier = 1.0
        for defending_type in defending_types:
            key = (defending_type.slug, attacking_slug)
            if key not in cls._multiplier_cache:
                cls._multiplier_cache[key] = defending_type.lookup_multiplier(
                    attacking_slug
                )
            mult_value = cls._multiplier_cache[key]
            multiplier *= mult_value
        return multiplier

    @classmethod
    def clear_cache(cls) -> None:
        cls._multiplier_cache.clear()

    def set_types(self, new_types: Sequence[str]) -> None:
        self._current_types = [Element.get(slug) for slug in new_types]

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
