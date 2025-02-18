# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.event import get_npc
from tuxemon.event.actions.common import CommonAction
from tuxemon.event.eventaction import EventAction


@final
@dataclass
class SetCharAttributeAction(EventAction):
    """
    Set the given attribute of the character to the given value.

    Script usage:
        .. code-block::

            set_char_attribute <character>,<attribute>,<value>

    Script parameters:
        character: Either "player" or character slug name (e.g. "npc_maple").
        attribute: Name of the attribute.
        value: Value of the attribute.

    """

    name = "set_char_attribute"
    character: str
    attribute: str
    value: str

    def start(self) -> None:
        character = get_npc(self.session, self.character)
        assert character
        CommonAction.set_entity_attribute(
            character, self.attribute, self.value
        )
