# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from tuxemon.event import MapCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.monster import MAX_MOVES
from tuxemon.session import Session


class CheckMaxTechCondition(EventCondition):
    """
    Check to see the player has at least one tuxemon with more
    than the max number of techniques.

    If yes, then it saves automatically the monster_id and
    inside a variable called "check_moves".

    Script usage:
        .. code-block::

            is check_max_tech [nr]

    Script parameters:
        nr: Number of tech, default the constant

    eg. "is check_max_tech standard"

    """

    name = "check_max_tech"

    def test(self, session: Session, condition: MapCondition) -> bool:
        player = session.player

        max_techs: int = 0
        max_techs = (
            MAX_MOVES
            if not condition.parameters
            else int(condition.parameters[0])
        )

        for monster in player.monsters:
            if len(monster.moves) > max_techs:
                player.game_variables["check_moves"] = str(
                    monster.instance_id.hex
                )
                player.game_variables["check_moves_monster"] = str(
                    monster.name.upper()
                )
                return True
        return False
