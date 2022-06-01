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
# Contributor(s):
#
# Adam Chevalier <chevalierAdam2@gmail.com>
#

from __future__ import annotations

from typing import NamedTuple, final

from tuxemon import prepare
from tuxemon.event.eventaction import EventAction
from tuxemon.locale import T
from tuxemon.menu.input import InputMenu


class RenamePlayerActionParameters(NamedTuple):
    pass


@final
class RenamePlayerAction(EventAction[RenamePlayerActionParameters]):
    """
    Open the text input screen to rename the player.

    Script usage:
        .. code-block::

            rename_player

    """

    name = "rename_player"
    param_class = RenamePlayerActionParameters

    def set_player_name(self, name: str) -> None:
        self.session.player.name = name

    def start(self) -> None:
        self.session.client.push_state(
            state_name=InputMenu,
            prompt=T.translate("input_name"),
            callback=self.set_player_name,
            escape_key_exits=False,
            initial=self.session.player.name,
            char_limit=prepare.PLAYER_NAME_LIMIT
        )

    def update(self) -> None:
        try:
            self.session.client.get_state_by_name(InputMenu)
        except ValueError:
            self.stop()
