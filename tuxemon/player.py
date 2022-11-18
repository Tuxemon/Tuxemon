#
# Tuxemon
# Copyright (C) 2014, William Edwards <shadowapex@gmail.com>,
#                     Benjamin Bean <superman2k5@gmail.com>
#
# This file is part of Tuxemon.
#
# Tuxemon is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Tuxemon is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Tuxemon.  If not, see <http://www.gnu.org/licenses/>.
#
# Contributor(s):
#
# William Edwards <shadowapex@gmail.com>
# Derek Clark <derekjohn.clark@gmail.com>
# Leif Theden <leif.theden@gmail.com>
#
# player
#

from __future__ import annotations

import datetime as dt
import logging

from tuxemon import prepare
from tuxemon.map import proj
from tuxemon.npc import NPC
from tuxemon.states.world.worldstate import WorldState

logger = logging.getLogger(__name__)


# Class definition for the player.
class Player(NPC):
    """Object for Players. WIP."""

    def __init__(
        self,
        npc_slug: str,
        world: WorldState,
    ) -> None:
        super().__init__(npc_slug, world=world)
        self.isplayer = True

        # Game variables for use with events
        self.game_variables = {"steps": 0}

    def update(self, time_delta: float) -> None:
        """
        Update the player movement around the game world.

        Increment the number of steps.

        Parameters:
            time_delta: A float of the time that has passed since
                the last frame. This is generated by clock.tick() / 1000.0.

        """
        # TODO: this will also record involuntary steps.
        # refactor so that only movements from the player are recorded.
        before = proj(self.position3)

        super().update(time_delta)

        after = proj(self.position3)

        diff_x = abs(after.x - before.x)
        diff_y = abs(after.y - before.y)

        self.game_variables["steps"] += diff_x + diff_y
        """
        %H - Hour 00-23
        %j - Day number of year 001-366
        """
        var = self.game_variables
        var["hour"] = int(dt.datetime.now().strftime("%H"))
        var["day_of_year"] = int(dt.datetime.now().strftime("%j"))

        # Day and night basic cycle (12h cycle)
        if int(var["hour"]) < 6:
            var["daytime"] = "false"
        elif 6 <= int(var["hour"]) < 18:
            var["daytime"] = "true"
        else:
            var["daytime"] = "false"

        # Day and night complex cycle (4h cycle)
        if int(var["hour"]) < 4:
            var["stage_of_day"] = "night"
        elif 4 <= int(var["hour"]) < 8:
            var["stage_of_day"] = "dawn"
        elif 8 <= int(var["hour"]) < 12:
            var["stage_of_day"] = "morning"
        elif 12 <= int(var["hour"]) < 16:
            var["stage_of_day"] = "afternoon"
        elif 16 <= int(var["hour"]) < 20:
            var["stage_of_day"] = "dusk"
        else:
            var["stage_of_day"] = "night"

        # Seasons
        if prepare.CONFIG.hemisphere == "north":
            if int(var["day_of_year"]) < 81:
                var["season"] = "winter"
            elif 81 <= int(var["day_of_year"]) < 173:
                var["season"] = "spring"
            elif 173 <= int(var["day_of_year"]) < 265:
                var["season"] = "summer"
            elif 265 <= int(var["day_of_year"]) < 356:
                var["season"] = "autumn"
            else:
                var["season"] = "winter"
        else:
            if int(var["day_of_year"]) < 81:
                var["season"] = "summer"
            elif 81 <= int(var["day_of_year"]) < 173:
                var["season"] = "autumn"
            elif 173 <= int(var["day_of_year"]) < 265:
                var["season"] = "winter"
            elif 265 <= int(var["day_of_year"]) < 356:
                var["season"] = "spring"
            else:
                var["season"] = "summer"
