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

from typing import NamedTuple, final

from tuxemon.event.eventaction import EventAction


class GetPlayerPartyActionParameters(NamedTuple):
    pass


@final
class GetPlayerPartyAction(EventAction[GetPlayerPartyActionParameters]):
    """
    Store the party monsters ids in Slot(number) variable.
    Slot0: instance_id, Slot1: instance_id, etc.

    Script usage:
        .. code-block::

            get_player_party

    """

    name = "get_player_party"
    param_class = GetPlayerPartyActionParameters

    def start(self) -> None:
        player = self.session.player
        slot = 0

        for monsters in player.monsters:
            player.game_variables[
                "slot" + str(slot)
            ] = monsters.instance_id.hex
            slot += 1
