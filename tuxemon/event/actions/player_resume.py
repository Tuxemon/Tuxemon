# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.states.world.worldstate import WorldState


@final
@dataclass
class PlayerResumeAction(EventAction):
    """
    Make the player resume movement.

    Script usage:
        .. code-block::

            player_resume

    """

    name = "player_resume"

    def start(self) -> None:
        # Get a copy of the world state.
        world = self.session.client.get_state_by_name(WorldState)

        world.menu_blocking = False
