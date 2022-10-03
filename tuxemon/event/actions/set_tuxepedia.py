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

from typing import NamedTuple, final

from tuxemon.db import SeenStatus
from tuxemon.event.eventaction import EventAction


class SetTuxepediaActionParameters(NamedTuple):
    monster_key: str
    monster_str: str


@final
class SetTuxepediaAction(EventAction[SetTuxepediaActionParameters]):
    """
    Set the key and value in the Tuxepedia dictionary.

    Script usage:
        .. code-block::

            set_tuxepedia <monster_slug>,<string>

    Script parameters:
        monster_slug: Monster slug name (e.g. "rockitten").
        string: seen / caught

    """

    name = "set_tuxepedia"
    param_class = SetTuxepediaActionParameters

    def start(self) -> None:
        player = self.session.player.tuxepedia

        # Read the parameters
        monster_key = self.parameters[0]
        monster_str = self.parameters[1]

        # Append the tuxepedia with a key
        if monster_str == "caught":
            player[str(monster_key)] = SeenStatus.caught
        elif monster_str == "seen":
            player[str(monster_key)] = SeenStatus.seen
