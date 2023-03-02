# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from tuxemon.event import MapCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session


class PlayerSpriteCondition(EventCondition):
    """
    Check the player's sprite

    Script usage:
        .. code-block::

            is player_sprite <sprite>

    """

    name = "player_sprite"

    def test(self, session: Session, condition: MapCondition) -> bool:
        """
        Check the player's sprite.

        Parameters:
            session: The session object
            condition: The map condition object.

        Returns:
            Whether the player has a specific sprite.

        """
        player = session.player
        sprite = condition.parameters[0]

        if player.template:
            for tmp in player.template:
                if tmp.sprite_name == sprite:
                    return True
                else:
                    return False
            return False
        return False
