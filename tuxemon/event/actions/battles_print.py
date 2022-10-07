#
# Tuxemon
# Copyright (c) 2014-2017 William Edwards <shadowapex@gmail.com>,
#                         Benjamin Bean <superman2k5@gmail.com>
#
# This file is part of Tuxemon
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event.eventaction import EventAction

logger = logging.getLogger(__name__)


@final
@dataclass
class BattlesAction(EventAction):
    """
    Print the current value of battle history to the console.

    If no variable is specified, print out values of all battles.

    Script usage:
        .. code-block::

            battles_print
            battles_print <variable>

        Script parameters:
            variable: Optional, prints out the value of this variable.

    """

    name = "battles_print"
    variable: Optional[str] = None

    def start(self) -> None:
        player = self.session.player

        variable = self.variable
        if variable:
            if variable in player.battle_history:
                print(f"{variable}: {player.battle_history[variable]}")
            else:
                print(f"'{variable}' has not been set yet.")
        else:
            print(player.battle_history)
