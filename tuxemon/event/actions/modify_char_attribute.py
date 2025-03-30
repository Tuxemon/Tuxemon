# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event import get_npc
from tuxemon.event.actions.common import CommonAction
from tuxemon.event.eventaction import EventAction

logger = logging.getLogger(__name__)


@final
@dataclass
class ModifyCharAttributeAction(EventAction):
    """
    Modify the given attribute of the character by modifier.

    By default this is achieved via addition, but prepending a '%' will cause
    it to be multiplied by the attribute.

    Script usage:
        .. code-block::

            modify_char_attribute <character>,<attribute>,<value>

    Script parameters:
        character: Either "player" or character slug name (e.g. "npc_maple").
        attribute: Name of the attribute to modify.
        value: Value of the attribute modifier.

    """

    name = "modify_char_attribute"
    character: str
    attribute: str
    value: str

    def start(self) -> None:
        character = get_npc(self.session, self.character)
        if character is None:
            logger.error(f"{self.character} not found")
            return
        CommonAction.modify_entity_attribute(
            character, self.attribute, self.value
        )
