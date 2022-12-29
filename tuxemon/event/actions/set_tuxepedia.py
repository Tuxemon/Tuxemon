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

from dataclasses import dataclass
from typing import final

from tuxemon.db import SeenStatus
from tuxemon.event.eventaction import EventAction


@final
@dataclass
class SetTuxepediaAction(EventAction):
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
    monster_key: str
    monster_str: str

    def start(self) -> None:
        player = self.session.player.tuxepedia

        # Append the tuxepedia with a key
        if self.monster_str == "caught":
            player[str(self.monster_key)] = SeenStatus.caught
        elif self.monster_str == "seen":
            player[str(self.monster_key)] = SeenStatus.seen
