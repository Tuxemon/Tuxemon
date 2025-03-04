# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass

from tuxemon.event import MapCondition, get_npc
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@dataclass
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
        _character, _monster, _label = condition.parameters

        character = get_npc(session, _character)
        if character is None:
            raise ValueError(f"{_character} not found")

        if _label == "seen":
            return character.tuxepedia.is_seen(_monster)
        elif _label == "caught":
            return character.tuxepedia.is_caught(_monster)
        else:
            raise ValueError(f"{_label} must be 'seen' or 'caught'")
