# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from typing import TYPE_CHECKING

from tuxemon.constants.asset_loader import fetch_asset
from tuxemon.entity.npc import NPC
from tuxemon.locale.locale import T

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.database.config import ModMetadata
    from tuxemon.session import Session

logger = logging.getLogger(__name__)


class GameLauncher:
    """
    Coordinates launching a game session based on mod metadata.
    Handles map loading, spawn position, state transitions, and initial game variables.
    """

    def __init__(self, client: BaseClient) -> None:
        """
        Parameters:
            client: The game client responsible for managing states and events.
        """
        self.client = client

    def launch(
        self,
        session: Session,
        meta: ModMetadata,
        remove_states: list[str] | None = None,
    ) -> None:
        """
        Starts the game session from a mod's metadata.

        Parameters:
            session: The active game session object.
            meta: The name (folder) of the mod to launch.
            remove_states: Optional list of state names to remove after launch.
        """
        logger.info(f"Launching mod '{meta.name}' version {meta.version}")

        tile_pos = meta.starting_position
        map_path = fetch_asset("maps", meta.starting_map)
        player_slug = random.choice(meta.starting_players)

        NPC.create_player(session, slug=player_slug)

        self.client.push_state(
            "WorldState", session=session, map_name=map_path
        )

        execute = self.client.event_engine

        # Teleport the player to the initial position
        teleport = ["player", meta.starting_map, tile_pos[0], tile_pos[1]]
        execute.execute_action("teleport", teleport)

        # Set money
        starting_money = random.randint(*meta.starting_money)
        execute.execute_action("set_money", ["player", starting_money])

        # Set name
        name = (
            meta.starting_names[0]
            if len(meta.starting_names) == 1
            else random.choice(meta.starting_names)
        )
        session.player.name = T.translate(name)

        # Set template
        template = ["player", meta.sprite, meta.combat_sheet]
        execute.execute_action("set_template", template)

        # Optionally clean up states
        if remove_states:
            for state in remove_states:
                self.client.remove_state_by_name(state)
