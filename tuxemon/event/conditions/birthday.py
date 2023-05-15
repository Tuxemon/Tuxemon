# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from tuxemon.event import MapCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session


class BirthdayCondition(EventCondition):
    """
    Check to see if birthday.

    Script usage:
        .. code-block::

            is birthday

    """

    name = "birthday"

    def test(self, session: Session, condition: MapCondition) -> bool:
        player = session.player
        if player.dob > 0:
            day_of_year = int(player.game_variables["day_of_year"])
            if player.dob == day_of_year:
                return True
            else:
                return False
        else:
            return False
