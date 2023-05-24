from __future__ import annotations

import logging

from tuxemon.event import MapCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session

logger = logging.getLogger(__name__)


class HasPartyBreederCondition(EventCondition):
    """
    Check to see if the player has a male and female
    monsters not basic (first evolution stage)
    in the party.

    Script usage:
        .. code-block::

            is has_party_breeder

    """

    name = "has_party_breeder"

    def test(self, session: Session, condition: MapCondition) -> bool:
        """
        Check to see if the player has a technique in his party.

        Parameters:
            session: The session object
            condition: The map condition object.

        Returns:
            Whether the player has a technique in his party.

        """
        player = session.player
        if any(
            t
            for t in player.monsters
            if t.stage != "basic" and t.gender == "male"
        ):
            if any(
                t
                for t in player.monsters
                if t.stage != "basic" and t.gender == "female"
            ):
                return True

        logger.info(f"No breeding monsters available")
        return False
