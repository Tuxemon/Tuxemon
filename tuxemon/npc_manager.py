# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import uuid
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, Optional

from tuxemon import networking

if TYPE_CHECKING:
    from tuxemon.client import LocalPygameClient
    from tuxemon.monster import Monster
    from tuxemon.npc import NPC


class NPCManager:
    def __init__(self) -> None:
        self.npcs: dict[str, NPC] = {}
        self.npcs_off_map: dict[str, NPC] = {}

    def npc_exists(self, slug: str) -> bool:
        return slug in self.npcs

    def add_npc(self, npc: NPC) -> None:
        self.npcs[npc.slug] = npc

    def add_npc_off_map(self, npc: NPC) -> None:
        self.npcs_off_map[npc.slug] = npc

    def remove_npc(self, slug: str) -> None:
        if slug in self.npcs:
            self.npcs[slug].remove_collision()
            del self.npcs[slug]

    def remove_npc_off_map(self, slug: str) -> None:
        """Removes an NPC off-map, ensuring cleanup."""
        if slug in self.npcs_off_map:
            self.npcs_off_map[slug].remove_collision()
            del self.npcs_off_map[slug]

    def get_npc(self, slug: str) -> Optional[NPC]:
        return self.npcs.get(slug)

    def get_npc_off_map(self, slug: str) -> Optional[NPC]:
        return self.npcs_off_map.get(slug)

    def get_npc_by_iid(self, iid: uuid.UUID) -> Optional[NPC]:
        return next(
            (npc for npc in self.npcs.values() if npc.instance_id == iid), None
        )

    def get_npc_off_map_by_iid(self, iid: uuid.UUID) -> Optional[NPC]:
        return next(
            (
                npc
                for npc in self.npcs_off_map.values()
                if npc.instance_id == iid
            ),
            None,
        )

    def get_entity_pos(self, pos: tuple[int, int]) -> Optional[NPC]:
        return next(
            (npc for npc in self.npcs.values() if npc.tile_pos == pos), None
        )

    def update_npcs_off_map(
        self, time_delta: float, client: LocalPygameClient
    ) -> None:
        """Updates NPCs off-map and synchronizes their positions."""
        for entity in self.npcs_off_map.values():
            entity.update(time_delta)
            if entity.update_location:
                char_dict = {"tile_pos": entity.final_move_dest}
                networking.update_client(entity, char_dict, client)
                entity.update_location = False

    def update_npcs(
        self, time_delta: float, client: LocalPygameClient
    ) -> None:
        """Updates NPCs and synchronizes their positions."""
        for entity in self.npcs.values():
            entity.update(time_delta)
            if entity.update_location:
                char_dict = {"tile_pos": entity.final_move_dest}
                networking.update_client(entity, char_dict, client)
                entity.update_location = False

    def clear_npcs(self) -> None:
        self.npcs.clear()
        self.npcs_off_map.clear()

    def get_all_entities(self) -> Sequence[NPC]:
        return list(self.npcs.values())

    def get_all_monsters(self) -> list[Monster]:
        return [
            monster for npc in self.npcs.values() for monster in npc.monsters
        ]

    def get_monster_by_iid(self, iid: uuid.UUID) -> Optional[Monster]:
        return next(
            (
                monster
                for npc in self.npcs.values()
                for monster in npc.monsters
                if monster.instance_id == iid
            ),
            None,
        )

    def add_clients_to_map(
        self, registry: Mapping[str, Any], current_map: str
    ) -> None:
        """
        Add players in the current map as NPCs.

        Parameters:
            registry: Locally hosted Neteria client/server registry.
            current_map: The name of the current map.
        """
        self.clear_npcs()
        for client in registry.values():
            if "sprite" in client:
                sprite = client["sprite"]
                client_map = client["map_name"]

                if client_map == current_map:
                    self.npcs[sprite.slug] = sprite
                    self.npcs_off_map.pop(sprite.slug, None)

                elif client_map != current_map:
                    self.npcs_off_map[sprite.slug] = sprite
                    self.npcs.pop(sprite.slug, None)
