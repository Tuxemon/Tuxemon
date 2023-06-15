# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction


@final
@dataclass
class StopCinemaModeAction(EventAction):
    """
    Stop cinema mode by animating black bars back to the normal aspect ratio.

    Script usage:
        .. code-block::

            stop_cinema_mode

    """

    name = "stop_cinema_mode"

    def start(self) -> None:
        player = self.session.player
        player.game_variables["cinema_mode"] = "off"
