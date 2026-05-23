# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.constants.asset_loader import fetch_asset
from tuxemon.entity.npc import NPC
from tuxemon.event.eventaction import EventAction
from tuxemon.platform.const.sizes import PLAYER_NPC
from tuxemon.save_system.save_manager import SaveManager
from tuxemon.save_system.save_slots import resolve_save_index
from tuxemon.session import Session
from tuxemon.states.world_state import WorldState

logger = logging.getLogger(__name__)


@final
@dataclass
class LoadGameAction(EventAction):
    """
    Loads a game from a specific save slot.

    The `index` parameter normally refers to the UI slot index (0-2).
    When `is_raw_slot` is False (default), the index is interpreted as a
    UI-facing slot and converted to an actual save slot number using
    `resolve_save_index()`.

    When `is_raw_slot` is True, the index is treated as a *raw* save slot
    number and used directly. This is primarily intended for internal or
    system-driven loads (e.g., autosave recovery).

    Script usage:
        .. code-block::

            load_game <index>

    Script parameters:
        index: UI slot index (0-2) unless `is_raw_slot=True`.
        is_raw_slot: If True, bypasses UI-to-slot conversion.
    """

    name = "load_game"
    index: int
    is_raw_slot: bool = False

    def start(self, session: Session) -> None:
        client = session.client
        slot = (
            self.index if self.is_raw_slot else resolve_save_index(self.index)
        )

        client.map_loader.clear_cache()
        logger.info("Loading!")

        save_data = SaveManager.load(slot)
        if not save_data:
            self.stop()
            return

        try:
            old_world = client.get_state_by_name(WorldState)
            client.remove_state_by_name("LoadMenuState")
            client.pop_state(old_world)
            client.remove_state_by_name("WorldMenuState")
        except ValueError:
            client.remove_state_by_name("LoadMenuState")
            client.remove_state_by_name("StartState")

        npc_state = save_data.npc_state
        if npc_state is None:
            logger.error("Save data missing NPC state.")
            self.stop()
            return

        slug = npc_state.player_slug or PLAYER_NPC
        npc_state.player_slug = slug
        NPC.create_player(session, slug=slug)

        if npc_state.current_map is None:
            logger.error("Save data missing current map.")
            self.stop()
            return

        map_path = fetch_asset("maps", npc_state.current_map)
        client.push_state("WorldState", session=session, map_name=map_path)

        session.load_state(save_data)
        session.current_slot = slot

        if npc_state.tile_pos is None:
            logger.error("Save data missing tile position.")
            self.stop()
            return

        tele_x, tele_y = npc_state.tile_pos
        params = ["player", npc_state.current_map, tele_x, tele_y]
        client.current_music.stop()
        client.event_engine.execute_action("teleport", params)
