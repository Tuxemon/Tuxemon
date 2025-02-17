# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from tuxemon.event import MapCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session


class TrueCondition(EventCondition):
    """
    This condition always returns true.

    Script usage:
        .. code-block::

            is true

    """

    name = "true"

    def test(self, session: Session, condition: MapCondition) -> bool:
        """
        This function always returns true.

        Parameters:
            session: The session object
            condition: The map condition object.

        Returns:
            Always ``True``.

        """
        return True
