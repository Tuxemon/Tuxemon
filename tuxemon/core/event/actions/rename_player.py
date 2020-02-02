# -*- coding: utf-8 -*-
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

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from tuxemon.core.event.eventaction import EventAction

class RenamePlayerAction(EventAction):
    """Opens the text input screen to rename the player.

    Valid Parameters: None
    """
    name = "rename_player"
    valid_parameters = []


    def set_player_name(name):
        world = self.game.get_state_name("WorldState")
        if world:
            world.player1.name = name

    def start(self):
        print("starting rename_player")
        # Get a copy of the world state.
        world = self.game.get_state_name("WorldState")
        if not world:
            return

        self.game.push_state(
            state_name="InputMenu",
            prompt=T.translate("input_name"),
            callback=set_player_name,
            escape_key_exits=True,
            initial=world.player1.name
        )

    def update(self):
        if self.game.get_state_name("InputMenu") is None:
            self.stop()

