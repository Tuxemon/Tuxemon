# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import ClassVar

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

    name: ClassVar[str] = "has_tuxepedia"
    character: str
    monster: str
    label: str

    def test(self, session: Session) -> bool:
        character = session.client.get_npc(self.character)
        if character is None:
            raise ValueError(f"{self.character} not found")

        if self.label == "seen":
            return character.tuxepedia.is_seen(self.monster)
        elif self.label == "caught":
            return character.tuxepedia.is_caught(self.monster)
        else:
            raise ValueError(f"{self.label} must be 'seen' or 'caught'")
