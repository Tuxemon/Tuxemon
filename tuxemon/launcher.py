# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from typing import TYPE_CHECKING, Optional

from tuxemon.constants.asset_loader import fetch_asset
from tuxemon.player import Player
from tuxemon.time_handler import today_ordinal

if TYPE_CHECKING:
    from tuxemon.client import LocalPygameClient
    from tuxemon.db import ModData
    from tuxemon.session import Session


class GameLauncher:
    """
    Coordinates launching a game session based on mod metadata.
    Handles map loading, spawn position, state transitions, and initial game variables.
    """

    def __init__(self, client: LocalPygameClient, db: ModData) -> None:
        """
        Parameters:
            client: The game client responsible for managing states and events.
            db: ModData instance providing access to mod metadata.
        """
        self.client = client
        self.db = db

    def launch(
        self,
        session: Session,
        mod_name: str,
        remove_states: Optional[list[str]] = None,
    ) -> None:
        """
        Starts the game session from a mod's metadata.

        Parameters:
            session: The active game session object.
            mod_name: The name (folder) of the mod to launch.
            remove_states: Optional list of state names to remove after launch.
        """
        destination = self.db.require_mod_attribute(mod_name, "starting_map")
        tile_pos = self.db.require_mod_attribute(mod_name, "starting_position")
        map_path = fetch_asset("maps", destination)

        player_slugs: list[str] = self.db.require_mod_attribute(
            mod_name, "starting_players"
        )
        player_slug = random.choice(player_slugs)

        Player.create(session, slug=player_slug)

        self.client.push_state(
            "WorldState", session=session, map_name=map_path
        )

        execute = self.client.event_engine

        # Teleport the player to the initial position
        params = ["player", map_path, tile_pos[0], tile_pos[1]]
        execute.execute_action("teleport", params)

        # Set money
        money_range: list[int] = self.db.require_mod_attribute(
            mod_name, "starting_money"
        )
        starting_money = random.randint(money_range[0], money_range[1])
        execute.execute_action("set_money", ["player", starting_money])

        # Set name
        names: list[str] = self.db.require_mod_attribute(
            mod_name, "starting_names"
        )
        if not names:
            raise ValueError(f"'starting_names' is empty")
        name = names[0] if len(names) == 1 else random.choice(names)
        execute.execute_action("set_player_name", [name])

        # Set template
        sprite = self.db.require_mod_attribute(mod_name, "sprite")
        combat = self.db.require_mod_attribute(mod_name, "combat_front")
        execute.execute_action("set_template", ["player", sprite, combat])

        # Record session metadata
        session.player.game_variables.set("date_start_game", today_ordinal())

        # Optionally clean up states
        if remove_states:
            for state in remove_states:
                self.client.remove_state_by_name(state)
