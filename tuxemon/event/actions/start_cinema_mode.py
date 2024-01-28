# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction


@final
@dataclass
class StartCinemaModeAction(EventAction):
    """
    Start cinema mode by animating black bars to narrow the aspect ratio.

    Script usage:
        .. code-block::

            start_cinema_mode

    """

    name = "start_cinema_mode"

    def start(self) -> None:
        player = self.session.player
        player.game_variables["cinema_mode"] = "on"
