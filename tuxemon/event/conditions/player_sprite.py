# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from tuxemon.event import MapCondition, get_npc
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session


class PlayerSpriteCondition(EventCondition):
    """
    Check the player's sprite

    Script usage:
        .. code-block::

            is npc_sprite <character>,<sprite>

    Script parameters:
        character: Either "player" or npc slug name (e.g. "npc_maple")
        sprite: NPC's sprite (eg maniac, florist, etc.)

    """

    name = "player_sprite"

    def test(self, session: Session, condition: MapCondition) -> bool:
        npc = get_npc(session, condition.parameters[0])
        if not npc:
            return False

        sprite = condition.parameters[1]

        if npc.template:
            for template in npc.template:
                if template.sprite_name == sprite:
                    return True
        return False
