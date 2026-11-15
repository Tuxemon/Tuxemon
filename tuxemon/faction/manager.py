# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from tuxemon.db import (
    FactionAlignment,
    FactionRelationStatus,
)
from tuxemon.faction.faction import Faction

if TYPE_CHECKING:
    from tuxemon.event.eventbus import EventBus
    from tuxemon.npc_manager import NPCManager
    from tuxemon.session import Session

logger = logging.getLogger(__name__)


class FactionManager:
    """Centralized manager for all faction operations."""

    def __init__(self, event_bus: EventBus) -> None:
        self._event_bus = event_bus
        self._factions: dict[str, Faction] = {}
        self._membership_cache: dict[str, list[Faction]] = {}
        self._maintenance_interval: float = 600.0
        self._maintenance_timer: float = 0.0

    def update(self, dt: float, session: Session) -> None:
        if not self._factions:
            return

        self._maintenance_timer += dt

        for faction in self._factions.values():
            faction.update(dt)

        if self._maintenance_timer >= self._maintenance_interval:
            self._maintenance_timer = 0.0

            for faction in self._factions.values():
                for npc_id in faction.members:
                    faction.evaluate_rank_change(
                        npc_id, session.player.variable_manager
                    )
            self.clear_membership_cache()

    def load_core_factions(self, faction_slugs: list[str]) -> None:
        if not faction_slugs:
            logger.info("No faction slugs provided to load core factions.")
            return

        for slug in faction_slugs:
            try:
                faction = Faction(event_bus=self._event_bus)
                faction.load_from_db(slug)
                self.register(faction)
                logger.debug(f"Successfully loaded core faction: {slug}")
            except Exception as e:
                logger.error(
                    f"Failed to load core faction '{slug}' via lookup: {e}",
                    exc_info=True,
                )

    def register(self, faction: Faction) -> None:
        if faction.slug in self._factions:
            logger.warning(
                f"Faction '{faction.slug}' already registered. Overwriting."
            )
        if not faction._event_bus:
            faction._event_bus = self._event_bus
        self._factions[faction.slug] = faction
        logger.debug(f"Registered faction: {faction.slug}")
        self.on_faction_loaded(faction)

    def on_faction_loaded(self, faction: Faction) -> None:
        logger.info(f"FactionManager detected faction loaded: {faction.slug}")

    def get(self, slug: str) -> Faction | None:
        return self._factions.get(slug)

    def all_factions(self) -> list[Faction]:
        return list(self._factions.values())

    def is_loaded(self, slug: str) -> bool:
        """Checks whether a faction with the given slug is registered."""
        return slug in self._factions

    def get_factions_by_member(self, npc_id: str) -> list[Faction]:
        """
        Returns a list of Faction instances that the given NPC is a member of.
        """
        if npc_id in self._membership_cache:
            return self._membership_cache[npc_id]

        member_factions = [
            faction
            for faction in self._factions.values()
            if faction.has_member(npc_id)
        ]
        self._membership_cache[npc_id] = member_factions
        return member_factions

    def clear_membership_cache(self, npc_id: str | None = None) -> None:
        """Clears membership cache for one or all NPCs."""
        if npc_id:
            self._membership_cache.pop(npc_id, None)
        else:
            self._membership_cache.clear()

    def resolve_diplomacy(self, slug_a: str, slug_b: str) -> None:
        """Custom logic to adjust relations or trigger events."""
        fa = self.get(slug_a)
        fb = self.get(slug_b)
        if not fa or not fb:
            logger.warning("One or both factions not found.")
            return

        if fa.alignment == fb.alignment:
            fa.set_relation(slug_b, FactionRelationStatus.ALLY)
            fb.set_relation(slug_a, FactionRelationStatus.ALLY)
            logger.info(f"{fa.slug} and {fb.slug} are now allies.")
        else:
            fa.set_relation(slug_b, FactionRelationStatus.RIVAL)
            fb.set_relation(slug_a, FactionRelationStatus.RIVAL)
            logger.info(f"{fa.slug} and {fb.slug} are now rivals.")

    def find_factions_by_alignment(
        self, alignment: FactionAlignment
    ) -> list[Faction]:
        return [f for f in self._factions.values() if f.alignment == alignment]

    def rank_npc_globally(self, npc_id: str) -> dict[str, str | None]:
        """Returns a map of faction slugs to NPC ranks based on reputation."""
        return {
            slug: faction.get_rank_for_reputation(
                faction.get_reputation(npc_id)
            )
            for slug, faction in self._factions.items()
        }

    def get_state(self, save_data: Mapping[str, Any]) -> None:
        self.clear_membership_cache()

        factions_save_data = save_data.get("factions_manager", {})
        if not factions_save_data:
            logger.info("No faction data found in save file.")
            return

        for faction_slug, faction_data in factions_save_data.items():
            faction = self.get(faction_slug)
            if not faction:
                logger.warning(
                    f"Faction '{faction_slug}' not registered. Skipping."
                )
                continue

            members_data = faction_data.get("members", {})
            public_rep = faction_data.get("public_reputation", 0)
            relations = faction_data.get("relations", {})
            faction.from_save_data(members_data, public_rep, relations)

    def set_state(self, npc_manager: NPCManager) -> dict[str, Any]:
        factions_save_data: dict[str, Any] = {}

        npc_slugs = npc_manager.get_all_slugs()
        for faction_slug, faction in self._factions.items():
            faction_data = faction.to_save_data(npc_slugs)
            if faction_data:
                factions_save_data[faction_slug] = faction_data

        return {"factions_manager": factions_save_data}
