# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID

from tuxemon.network.networking import CharData, update_client

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.monster import Monster
    from tuxemon.save_state import NPCState
    from tuxemon.session import Session
    from tuxemon.network.manager import NetworkManager
    from tuxemon.npc import NPC

logger = logging.getLogger(__name__)



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

    def get_npc_by_iid(self, iid: UUID) -> Optional[NPC]:
        return next(
            (npc for npc in self.npcs.values() if npc.instance_id == iid), None
        )

    def get_npc_off_map_by_iid(self, iid: UUID) -> Optional[NPC]:
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
        self, time_delta: float, client: BaseClient
    ) -> None:
        """Updates NPCs off-map and synchronizes their positions."""
        for entity in self.npcs_off_map.values():
            entity.update(time_delta)
            if entity.update_location:
                char_dict = CharData(
                    tile_pos=entity.final_move_dest,
                    name=entity.name,
                    facing=entity.facing,
                    monsters=[],
                    inventory=[],
                )
                update_client(entity, char_dict, client)
                entity.update_location = False

    def update_npcs(self, time_delta: float, client: BaseClient) -> None:
        """Updates NPCs and synchronizes their positions."""
        for entity in self.npcs.values():
            entity.update(time_delta)
            if entity.update_location:
                char_dict = CharData(
                    tile_pos=entity.final_move_dest,
                    name=entity.name,
                    facing=entity.facing,
                    monsters=[],
                    inventory=[],
                )
                update_client(entity, char_dict, client)
                entity.update_location = False

    def clear_npcs(self) -> None:
        npcs_to_keep: dict[str, NPC] = {}

        for slug, npc in self.npcs.items():
            if npc.persistence:
                npcs_to_keep[slug] = npc
            else:
                npc.remove_collision()

        self.npcs = npcs_to_keep

        npcs_off_map_to_keep: dict[str, NPC] = {}

        for slug, npc in self.npcs_off_map.items():
            if npc.persistence:
                npcs_off_map_to_keep[slug] = npc
            else:
                npc.remove_collision()

        self.npcs_off_map = npcs_off_map_to_keep

        logger.debug(
            f"NPCManager cleared non-persistent NPCs. "
            f"Kept {len(self.npcs)} on-map and {len(self.npcs_off_map)} off-map persistent NPCs."
        )

    def get_all_entities(self) -> Sequence[NPC]:
        return list(self.npcs.values())

    def get_all_monsters(self) -> list[Monster]:
        return [
            monster for npc in self.npcs.values() for monster in npc.monsters
        ]

    def get_monster_by_iid(self, iid: UUID) -> Optional[Monster]:
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
        self, registry: dict[str, Any], current_map: str
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

    def get_all_npc_slugs(self, include_off_map: bool = False) -> list[str]:
        """Returns all NPC slugs. Optionally includes off-map NPCs."""
        slugs = list(self.npcs.keys())
        if include_off_map:
            slugs.extend(self.npcs_off_map.keys())
        return slugs

    def get_persistent_npc_states(self, session: Session) -> list[NPCState]:
        """
        Returns a list of NPCStates for all persistent NPCs currently managed.
        This excludes the main player character, whose state is saved separately.
        """
        persistent_states = []
        player_slug = session.player.slug

        for npc in self.npcs.values():
            if npc.persistence and npc.slug != player_slug:
                if npc.session:
                    persistent_states.append(npc.get_state(npc.session))
                else:
                    logger.warning(
                        f"Cannot save persistent NPC {npc.slug}: session is missing."
                    )

        for npc in self.npcs_off_map.values():
            if npc.persistence and npc.slug != player_slug:
                if npc.session:
                    persistent_states.append(npc.get_state(npc.session))
                else:
                    logger.warning(
                        f"Cannot save persistent NPC off-map {npc.slug}: session is missing."
                    )

        return persistent_states

    def load_persistent_npc_states(
        self,
        session: Session,
        npc_states: list[NPCState],
    ) -> None:
        """
        Recreates and adds persistent NPCs from a list of saved states.
        This process bypasses the standard map loading, which normally clears
        all non-player NPCs.
        """
        if not npc_states:
            return

        current_map_name = session.client.get_map_name()

        for state in npc_states:
            if not state.player_slug:
                continue

            new_npc = NPC(npc_slug=state.player_slug, session=session)
            new_npc.set_state(session, state)

            if state.current_map == current_map_name:
                self.add_npc(new_npc)
                self.npcs_off_map.pop(state.player_slug, None)
            else:
                self.add_npc_off_map(new_npc)
                self.npcs.pop(state.player_slug, None)

            logger.debug(
                f"Loaded persistent NPC: {state.player_name} ({state.player_slug}) "
                f"on map {state.current_map}. Current Map: {current_map_name}"
            )

    def handle_player_teleport(
        self,
        client: BaseClient,
        char: NPC,
        network: NetworkManager,
    ) -> None:
        """Handles NPC and player updates after teleport."""
        client.event_data["transition"] = False

        if network.is_connected():
            assert network.client
            current_map = client.get_map_name()
            self.add_clients_to_map(network.client.registry, current_map)
            network.client.update_player(char.facing.value)

        self.update_npcs(0, client)
        self.update_npcs_off_map(0, client)
