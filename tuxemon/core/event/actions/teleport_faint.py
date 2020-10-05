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

from tuxemon.core.event.eventaction import EventAction


class TeleportFaintAction(EventAction):
    name = "teleport_faint"

    def start(self):
        player = self.session.player

        # Start with the default value, override if game variable exists
        teleport = ["healing_center.tmx", 7, 10]
        if 'teleport_faint' in player.game_variables:
            teleport = player.game_variables['teleport_faint'].split(" ")

        # Start the screen transition
        # self.game.event_engine.execute_action("screen_transition", [.3])

        # Call the teleport action
        self.session.client.event_engine.execute_action("teleport", teleport)
