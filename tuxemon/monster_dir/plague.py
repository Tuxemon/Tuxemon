# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any, Optional

from tuxemon.db import (
    PlagueType,
)

logger = logging.getLogger(__name__)


class MonsterPlagueHandler:
    """
    Manages the various plagues affecting a monster.
    """

    def __init__(
        self, plagues: Optional[dict[str, PlagueType]] = None
    ) -> None:
        self._plagues = plagues or {}

    @property
    def current_plagues(self) -> dict[str, PlagueType]:
        return self._plagues

    def infect(self, plague_slug: str) -> None:
        self._plagues[plague_slug] = PlagueType.infected

    def inoculate(self, plague_slug: str) -> None:
        self._plagues[plague_slug] = PlagueType.inoculated

    def is_infected(self) -> bool:
        return any(
            plague_type == PlagueType.infected
            for plague_type in self._plagues.values()
        )

    def remove_plague(self, plague_slug: str) -> None:
        if plague_slug in self._plagues:
            del self._plagues[plague_slug]

    def has_plague(self, plague_slug: str) -> bool:
        return plague_slug in self._plagues

    def get_plague_type(self, plague_slug: str) -> Optional[PlagueType]:
        type_str = self._plagues.get(plague_slug)
        if type_str:
            return PlagueType(type_str)
        return None

    def get_infected_slugs(self) -> list[str]:
        return [
            slug
            for slug, plague in self._plagues.items()
            if plague == PlagueType.infected
        ]

    def is_infected_with(self, plague_slug: str) -> bool:
        return self.get_plague_type(plague_slug) == PlagueType.infected

    def is_inoculated_against(self, plague_slug: str) -> bool:
        return self.get_plague_type(plague_slug) == PlagueType.inoculated

    def clear_plagues(self) -> None:
        self._plagues.clear()

    def encode_plagues(self) -> dict[str, PlagueType]:
        return self._plagues.copy()

    def decode_plagues(self, json_data: Optional[Mapping[str, Any]]) -> None:
        if json_data and "plague" in json_data:
            self._plagues.update(json_data["plague"])
