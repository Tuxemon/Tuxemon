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

from tuxemon.event.eventaction import EventAction
import logging

logger = logging.getLogger(__name__)


# noinspection PyAttributeOutsideInit
class ClearVariableAction(EventAction):
    """Clears the value of var from the game.

    Valid Parameters: string variable_name

    **Examples:**

    >>> EventAction.__dict__
    {
        "type": "clear_variable",
        "parameters": [
            "variable"
        ]
    }

    """

    name = "clear_variable"
    valid_parameters = [(str, "variable")]

    def start(self):
        player = self.session.player
        key = self.parameters.variable
        player.game_variables.pop(key, None)
