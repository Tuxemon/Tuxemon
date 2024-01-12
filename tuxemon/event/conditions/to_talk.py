# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from tuxemon.event import MapCondition
from tuxemon.event.conditions.button_pressed import ButtonPressedCondition
from tuxemon.event.conditions.char_facing_char import CharFacingCharCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session


class ToTalkCondition(EventCondition):
    """
    Check if a character is attempting to talk to another character.

    Script usage:
        .. code-block::

            is to_talk <character1>,<character2>

    Script parameters:
        character1: Either "player" or character slug name (e.g. "npc_maple").
        character2: Either "player" or character slug name (e.g. "npc_maple").

    """

    name = "to_talk"

    def test(self, session: Session, condition: MapCondition) -> bool:
        char_facing_char = CharFacingCharCondition().test(
            session,
            condition,
        )
        button_pressed = ButtonPressedCondition().test(
            session,
            MapCondition(
                type="button_pressed",
                parameters=[
                    "K_RETURN",
                ],
                operator="is",
                width=0,
                height=0,
                x=0,
                y=0,
                name="",
            ),
        )
        return char_facing_char and button_pressed
