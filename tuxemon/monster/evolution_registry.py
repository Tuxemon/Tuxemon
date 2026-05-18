# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any
from uuid import UUID

logger = logging.getLogger(__name__)


@dataclass
class MissedEvolution:
    slug: str
    level: int
    count: int


class EvolutionRegistry:
    def __init__(self) -> None:
        self._missed_evolutions: dict[UUID, list[MissedEvolution]] = {}
        self._pending_evolutions: dict[UUID, list[str]] = {}
        self._blocked_evolutions: dict[UUID, set[str]] = {}

    def log_missed(
        self, monster_id: UUID, evolution_slug: str, level: int
    ) -> None:
        evolutions = self._missed_evolutions.setdefault(monster_id, [])

        for evo in evolutions:
            if evo.slug == evolution_slug and evo.level == level:
                evo.count += 1
                logger.debug(
                    f"Incremented refusal count for {evo.slug} at level {evo.level} (count={evo.count})"
                )
                return

        evolutions.append(
            MissedEvolution(slug=evolution_slug, level=level, count=1)
        )
        logger.debug(
            f"Logged missed evolution: {evolution_slug} at level {level} (count=1)"
        )

    def get_retryable_missed(
        self, monster_id: UUID, max_attempts: int = 3
    ) -> list[str]:
        retryable = [
            evo.slug
            for evo in self._missed_evolutions.get(monster_id, [])
            if evo.count < max_attempts
        ]
        logger.debug(
            f"Retryable missed evolutions for {monster_id}: {retryable}"
        )
        return retryable

    def clear_missed(
        self, monster_id: UUID, evolution_slug: str | None = None
    ) -> None:
        if monster_id not in self._missed_evolutions:
            logger.debug(f"No missed evolutions to clear for {monster_id}")
            return

        if evolution_slug is None:
            del self._missed_evolutions[monster_id]
            logger.debug(f"Cleared all missed evolutions for {monster_id}")
        else:
            original = self._missed_evolutions[monster_id]
            filtered = [evo for evo in original if evo.slug != evolution_slug]

            if filtered:
                self._missed_evolutions[monster_id] = filtered
            else:
                del self._missed_evolutions[monster_id]

            logger.debug(
                f"Cleared missed evolution '{evolution_slug}' for {monster_id}"
            )

    def add_pending(self, monster_id: UUID, evolution_slug: str) -> None:
        self._pending_evolutions.setdefault(monster_id, []).append(
            evolution_slug
        )
        logger.debug(
            f"Added pending evolution '{evolution_slug}' for {monster_id}"
        )

    def get_pending(self, monster_id: UUID) -> list[str]:
        pending = self._pending_evolutions.get(monster_id, [])
        logger.debug(f"Pending evolutions for {monster_id}: {pending}")
        return pending

    def clear_pending(self, monster_id: UUID) -> None:
        if monster_id in self._pending_evolutions:
            logger.debug(f"Cleared pending evolutions for {monster_id}")
        else:
            logger.debug(f"No pending evolutions to clear for {monster_id}")
        self._pending_evolutions.pop(monster_id, None)

    def get_blocked(self, monster_id: UUID) -> set[str]:
        """Returns the set of blocked evolution slugs for a monster."""
        return self._blocked_evolutions.get(monster_id, set())

    def block_evolution_forever(
        self, monster_id: UUID, evolution_slug: str
    ) -> None:
        """Adds a specific evolution to the permanent block list."""
        self._blocked_evolutions.setdefault(monster_id, set()).add(
            evolution_slug
        )
        self.clear_missed(monster_id, evolution_slug)
        self.clear_pending_slug(monster_id, evolution_slug)
        logger.debug(
            f"Permanently blocked evolution '{evolution_slug}' for {monster_id}"
        )

    def unblock_evolution(self, monster_id: UUID, evolution_slug: str) -> None:
        """Removes a specific evolution from the permanent block list."""
        if monster_id in self._blocked_evolutions:
            self._blocked_evolutions[monster_id].discard(evolution_slug)
            if not self._blocked_evolutions[monster_id]:
                del self._blocked_evolutions[monster_id]
            logger.debug(
                f"Unblocked evolution '{evolution_slug}' for {monster_id}"
            )
        else:
            logger.debug(
                f"Evolution '{evolution_slug}' for {monster_id} was not blocked."
            )

    def clear_pending_slug(
        self, monster_id: UUID, evolution_slug: str
    ) -> None:
        """Removes a specific evolution slug from the pending list."""
        if monster_id in self._pending_evolutions:
            self._pending_evolutions[monster_id] = [
                slug
                for slug in self._pending_evolutions[monster_id]
                if slug != evolution_slug
            ]

    def encode_registry(self) -> Mapping[str, Any]:
        return {
            "missed": {
                monster_id.hex: [
                    {"slug": evo.slug, "level": evo.level, "count": evo.count}
                    for evo in evolutions
                ]
                for monster_id, evolutions in self._missed_evolutions.items()
            },
            "pending": {
                monster_id.hex: slugs
                for monster_id, slugs in self._pending_evolutions.items()
            },
            "blocked": {
                monster_id.hex: list(slugs)
                for monster_id, slugs in self._blocked_evolutions.items()
            },
        }

    def decode_registry(self, data: Mapping[str, Any]) -> None:
        self._missed_evolutions.clear()
        self._pending_evolutions.clear()
        self._blocked_evolutions.clear()

        for monster_id_str, evolutions in data.get("missed", {}).items():
            monster_id = UUID(monster_id_str)
            self._missed_evolutions[monster_id] = [
                MissedEvolution(
                    slug=evo["slug"], level=evo["level"], count=evo["count"]
                )
                for evo in evolutions
            ]

        for monster_id_str, slugs in data.get("pending", {}).items():
            monster_id = UUID(monster_id_str)
            self._pending_evolutions[monster_id] = slugs

        for monster_id_str, slugs in data.get("blocked", {}).items():
            monster_id = UUID(monster_id_str)
            self._blocked_evolutions[monster_id] = set(slugs)
