# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging

from tuxemon.db import EvolutionStage, GenderType
from tuxemon.event import MapCondition, get_npc
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session

logger = logging.getLogger(__name__)


class HasPartyBreederCondition(EventCondition):
    """
    Check to see if the character has a male and female
    monsters not basic (first evolution stage) in the party.

    Script usage:
        .. code-block::

            is has_party_breeder <character>

    Script parameters:
        character: Either "player" or npc slug name (e.g. "npc_maple").

    """

    name = "has_party_breeder"

    def test(self, session: Session, condition: MapCondition) -> bool:
        _character = condition.parameters[0]
        basic = EvolutionStage.basic
        male = GenderType.male
        female = GenderType.female
        character = get_npc(session, _character)
        if character is None:
            logger.error(f"{_character} not found")
            return False
        party = character.monsters
        var1 = [
            mon for mon in party if mon.stage != basic and mon.gender == male
        ]
        var2 = [
            mon for mon in party if mon.stage != basic and mon.gender == female
        ]
        return any(var1) and any(var2)
