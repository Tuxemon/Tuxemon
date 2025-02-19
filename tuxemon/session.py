# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tuxemon.client import LocalPygameClient
    from tuxemon.player import Player
    from tuxemon.states.world.worldstate import WorldState


class Session:
    """
    Contains Client, World, and Player.

    Eventually this will be extended to support network sessions.
    """

    def __init__(
        self,
        client: LocalPygameClient,
        world: WorldState,
        player: Player,
    ) -> None:
        """
        Parameters:
            client: Game client.
            world: Game world.
            player: Player object.

        """
        self.client = client
        self.world = world
        self.player = player


# WIP will be filled in later when game starts
local_session = Session(None, None, None)  # type: ignore[arg-type]
