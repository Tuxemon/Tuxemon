#
# Tuxemon
# Copyright (c) 2020      William Edwards <shadowapex@gmail.com>,
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
# Contributor(s):
#
# Adam Chevalier <chevalierAdam2@gmail.com>

from __future__ import annotations
from tuxemon.event.eventaction import EventAction
import logging
from typing import NamedTuple, final

logger = logging.getLogger(__name__)


class ClearVariableActionParameters(NamedTuple):
    variable: str


# noinspection PyAttributeOutsideInit
@final
class ClearVariableAction(EventAction[ClearVariableActionParameters]):
    """Clears the value of var from the game.

    Valid Parameters: string variable_name
    """

    name = "clear_variable"
    param_class = ClearVariableActionParameters

    def start(self) -> None:
        player = self.session.player
        key = self.parameters.variable
        player.game_variables.pop(key, None)
