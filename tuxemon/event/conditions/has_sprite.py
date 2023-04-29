# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>

from tuxemon.event import MapCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session


class HasSpriteCondition(EventCondition):
    """
    Check to see if a NPC has a specific sprite.

    Script usage:
        .. code-block::

            is has_sprite <sprite>

    Script parameters:
        sprite: Sprite slug (eg. adventurer, heroine, swimmer, etc.)

    """

    name = "has_sprite"

    def test(self, session: Session, condition: MapCondition) -> bool:
        player = session.player
        if player.sprite_name == condition.parameters[0]:
            return True
        else:
            return False
