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

import datetime as dt
import logging
from typing import NamedTuple, Optional, final

from tuxemon.event.eventaction import EventAction

logger = logging.getLogger(__name__)


class BattlesPrintActionParameters(NamedTuple):
    character: Optional[str]
    result: Optional[str]


@final
class BattlesAction(EventAction[BattlesPrintActionParameters]):
    """
    Print the current value of battle history to the console.

    If no variable is specified, print out values of all battles.

    Script usage:
        .. code-block::

            battles_print
            battles_print [<character>,<result>]

        Script parameters:
            character: Npc slug name (e.g. "npc_maple").
            result: One among "won", "lost" or "draw"

    """

    name = "battles_print"
    param_class = BattlesPrintActionParameters

    def start(self) -> None:
        player = self.session.player
        today = dt.date.today().toordinal()

        value = (self.parameters.character, self.parameters.result)
        if self.parameters.result:
            if value[0] in player.battle_history:
                battle_date = player.battle_history.get(value)
                print(
                    f"{value[1]} against {value[0]} {today - battle_date} days ago"
                )
            else:
                print(f"Never {value[1]} against {value[0]}")
        else:
            print(player.battle_history)
