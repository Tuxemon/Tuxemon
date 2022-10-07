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

import logging
import random
from typing import NamedTuple, final

from tuxemon.event.eventaction import EventAction
from tuxemon.technique.technique import Technique

logger = logging.getLogger(__name__)


class TeachActionParameters(NamedTuple):
    monster_id: str
    technique: str


@final
class TeachAction(EventAction[TeachActionParameters]):
    """
    Teach a monster a technique.
    Script usage:
        .. code-block::
            teach [monster_id],<technique>
    Script parameters:
        monster_id: Id of the monster (name of the variable).
        technique: Slug of the technique (e.g. "bullet").
    """

    name = "teach"
    param_class = TeachActionParameters

    def start(self) -> None:
        player = self.session.player
        move = self.parameters.technique
        monster = player.find_monster_by_id(self.parameters.monster_id)
        if monster is None:
            mon = random.choice(self.session.player.monsters)
            mon.learn(Technique(move))
            logger.info("{} learned technique {}!".format(mon, move))
        else:
            if move in monster.moves:
                return
            else:
                monster.learn(Technique(move))
