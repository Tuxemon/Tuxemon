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

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.map import dirs2, get_direction
from tuxemon.npc import NPC


class NpcFaceActionParameters(NamedTuple):
    npc_slug: str
    direction: str


@final
class NpcFaceAction(EventAction[NpcFaceActionParameters]):
    """
    Make the NPC face a certain direction.

    Script usage:
        .. code-block::

            npc_face <npc_slug>,<direction>

    Script parameters:
        npc_slug: Either "player" or npc slug name (e.g. "npc_maple").
        direction: Direction to face. It can be: "left", "right", "up", "down",
             "player" or a npc slug.

    """

    name = "npc_face"
    param_class = NpcFaceActionParameters

    def start(self) -> None:
        npc = get_npc(self.session, self.parameters.npc_slug)
        assert npc
        direction = self.parameters.direction

        target: NPC
        if direction not in dirs2:
            if direction == "player":
                target = self.session.player
            else:
                maybe_target = get_npc(self.session, direction)
                assert maybe_target
                target = maybe_target
            direction = get_direction(npc.tile_pos, target.tile_pos)

        npc.facing = direction
