# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session


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

    def start(self, session: Session) -> None:
        session.client.map_renderer.cinema_x_ratio = None
        session.client.map_renderer.cinema_y_ratio = None
