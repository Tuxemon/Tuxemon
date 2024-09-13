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
        character = get_npc(session, _character)
        if character is None:
            logger.error(f"{_character} not found")
            return False

        has_male_evolved_monsters = any(
            mon.stage != EvolutionStage.basic and mon.gender == GenderType.male
            for mon in character.monsters
        )
        has_female_evolved_monsters = any(
            mon.stage != EvolutionStage.basic
            and mon.gender == GenderType.female
            for mon in character.monsters
        )

        return has_male_evolved_monsters and has_female_evolved_monsters
