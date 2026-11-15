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
class CharSpriteCondition(EventCondition):
    """
    Check the character's sprite

    Script usage:
        .. code-block::

            is char_sprite <character>,<sprite>

    Script parameters:
        character: Either "player" or character slug name (e.g. "npc_maple")
        sprite: NPC's sprite (eg maniac, florist, etc.)
    """

    name: ClassVar[str] = "char_sprite"
    character: str
    sprite: str

    def test(self, session: Session) -> bool:
        target = session.client.get_npc(self.character)
        if not target:
            return False

        return target.appearance_manager.state.sprite_name == self.sprite
