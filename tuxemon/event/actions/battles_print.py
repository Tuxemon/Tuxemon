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
        character = self.parameters.character
        result = self.parameters.result
        today = dt.date.today().toordinal()

        if character in player.battle_history:
            output, battle_date = player.battle_history[character]
            diff_date = today - battle_date
            if result == output:
                print(f"{result} against {character} {diff_date} days ago")
            else:
                print(f"Never {result} against {character}")
        else:
            print(player.battle_history)
