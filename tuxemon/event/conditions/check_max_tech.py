# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass

from tuxemon.event import MapCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.prepare import MAX_MOVES
from tuxemon.session import Session


@dataclass
class CheckMaxTechCondition(EventCondition):
    """
    Check to see the player has at least one tuxemon with more
    than the max number of techniques in its party.

    If yes, then it saves automatically the monster_id and
    inside the dictionary event_data.

    Script usage:
        .. code-block::

            is check_max_tech [nr]

    Script parameters:
        nr: Number of tech, default the constant

    eg. "is check_max_tech"
    eg. "is check_max_tech 2"

    """

    name = "check_max_tech"

    def test(self, session: Session, condition: MapCondition) -> bool:
        player = session.player
        max_techs = (
            MAX_MOVES
            if not condition.parameters
            else int(condition.parameters[0])
        )
        monsters = [
            monster
            for monster in player.monsters
            if len(monster.moves) > max_techs
        ]
        session.client.event_data[self.name] = monsters
        return bool(monsters)
