# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class UpdateTimeAction(EventAction):
    """
    Update time variables.

    Script usage:
        .. code-block::

            update_time player

    Script parameters:
        file: File to load.

    eg: "update_time player"
    """

    name = "update_time"
    character: str

    def start(self, session: Session) -> None:
        character = session.client.get_npc(self.character)
        if character is None:
            logger.error(f"{self.character} not found")
            self.stop()
            return

        time_vars = session.time.get_time_variables()
        game_variables = character.game_variables

        game_variables.set("hour", str(time_vars.hour))
        game_variables.set("day_of_year", str(time_vars.day_of_year))
        game_variables.set("year", str(time_vars.year))
        game_variables.set("weekday", time_vars.weekday)
        game_variables.set("leap_year", time_vars.leap_year)
        game_variables.set("daytime", time_vars.daytime)
        game_variables.set("stage_of_day", time_vars.stage_of_day)
        game_variables.set("season", time_vars.season)
