# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging

from tuxemon.db import SeenStatus
from tuxemon.event import MapCondition, get_npc
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session

logger = logging.getLogger(__name__)


class HasTuxepediaCondition(EventCondition):
    """
    Check if a monster is registered in Tuxepedia.

    Script usage:
        .. code-block::

            is has_tuxepedia <character>,<monster>,<label>

    Script parameters:
        character: Either "player" or npc slug name (e.g. "npc_maple").
        monster: Monster slug name (e.g. "rockitten").
        label: Either "seen" or "caught".
    """

    name = "has_tuxepedia"

    def test(self, session: Session, condition: MapCondition) -> bool:
        character, monster, label = condition.parameters

        character = get_npc(session, character)
        if character is None:
            raise ValueError(f"{character} not found")

        return (monster, SeenStatus(label)) in character.tuxepedia.items()
