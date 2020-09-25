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


from tuxemon.core.event.eventaction import EventAction
from tuxemon.core.locale import T


class RenamePlayerAction(EventAction):
    """Opens the text input screen to rename the player.

    Valid Parameters: None
    """
    name = "rename_player"
    valid_parameters = []

    def set_player_name(self, name):
        self.session.player.name = name

    def start(self):
        self.session.client.push_state(
            state_name="InputMenu",
            prompt=T.translate("input_name"),
            callback=self.set_player_name,
            escape_key_exits=False,
            initial=self.session.player.name
        )

    def update(self):
        if self.session.client.get_state_by_name("InputMenu") is None:
            self.stop()
