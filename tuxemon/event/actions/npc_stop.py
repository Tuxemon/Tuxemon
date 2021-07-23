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

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction


class NpcStopAction(EventAction):
    name = "npc_stop"

    def __init__(self, *args, **kwrags):
        super().__init__(*args, **kwrags)
        self.npc = None
        self.path = None
        self.path_origin = None

    def start(self):
        npc_slug = self.raw_parameters[0]
        self.npc = get_npc(self.session, npc_slug)

        engine = self.session.engine
        for task_id, actionlist in engine.running_events.items():
            action = actionlist.running_action
            if actionlist.running_action.context.name == "npc_move_tile":
                action.stop()

        self.session.engine.set_message("player_moved")
