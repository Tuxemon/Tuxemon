# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon import prepare
from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.time_handler import (
    calculate_day_night_cycle,
    calculate_day_stage_of_day,
    determine_season,
    get_current_time,
    is_leap_year,
)

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

    def start(self) -> None:
        character = get_npc(self.session, self.character)
        if character is None:
            logger.error(f"{self.character} not found")
            return

        current_time = get_current_time()
        game_variables = character.game_variables
        game_variables["hour"] = current_time.strftime("%H")
        game_variables["day_of_year"] = str(current_time.timetuple().tm_yday)
        game_variables["year"] = current_time.strftime("%Y")
        game_variables["weekday"] = current_time.strftime("%A")
        game_variables["leap_year"] = (
            "true" if is_leap_year(current_time.year) else "false"
        )
        game_variables["daytime"] = calculate_day_night_cycle(current_time)
        game_variables["stage_of_day"] = calculate_day_stage_of_day(
            current_time
        )
        game_variables["season"] = determine_season(
            current_time, prepare.CONFIG.hemisphere
        )
