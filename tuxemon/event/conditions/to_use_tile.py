# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from tuxemon.event.conditions.button_pressed import ButtonPressedCondition
from tuxemon.event.conditions.char_facing_tile import CharFacingTileCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session


@dataclass
class ToUseTileCondition(EventCondition):
    """
    Checks whether the player (or another character) is attempting to
    interact with the tile directly in front of them.

    Script usage:
        .. code-block::

            is to_use_tile <character>,<value>

    Script parameters:
        character: The character performing the interaction. Typically
            "player", but may also be an NPC slug (e.g. "npc_maple").
        value: Optional value passed through to the underlying
            CharFacingTileCondition. May be used to restrict which tile
            types can be interacted with, or left empty for general use.

    Behavior:
        - First checks whether the character is facing a valid tile using
          CharFacingTileCondition.
        - Then checks whether the INTERACT button was pressed.
        - Returns True only if both conditions are satisfied.

    Dataclass fields:
        character: str
            The character whose facing direction and tile interaction
            should be evaluated.
        value: str | None
            Optional tile-matching value forwarded to
            CharFacingTileCondition.
    """

    character: str
    value: str | None = None

    name: ClassVar[str] = "to_use_tile"

    def test(self, session: Session) -> bool:
        char_facing = CharFacingTileCondition(self.character, self.value).test(
            session
        )
        button_pressed = ButtonPressedCondition("INTERACT").test(session)
        return char_facing and button_pressed
