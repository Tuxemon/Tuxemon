# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from tuxemon.combat import has_status
from tuxemon.event import MapCondition, get_npc
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session


class PlayerDefeatedCondition(EventCondition):
    """
    Check to see the player has at least one tuxemon, and all tuxemon in their
    party are defeated.

    Script usage:
        .. code-block::

            is player_defeated [character]

    Script parameters:
        character: Either "player" or npc slug name (e.g. "npc_maple")

    """

    name = "player_defeated"

    def test(self, session: Session, condition: MapCondition) -> bool:
        slug = (
            "player" if not condition.parameters else condition.parameters[0]
        )
        player = get_npc(session, slug)
        if not player:
            return False

        if player.monsters:
            for mon in player.monsters:
                if mon.current_hp <= 0 and not has_status(mon, "faint"):
                    mon.faint()
                if "faint" not in (s.slug for s in mon.status):
                    return False
            return True
        return False
