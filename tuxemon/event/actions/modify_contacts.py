# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class ModifyContactsAction(EventAction):
    """
    Modify contact relationship.

    Script usage:
        .. code-block::

            modify_contacts <character>,<npc_slug>,<attribute>,<value>

    Script parameters:
        character: Either "player" or character slug name (e.g. "npc_maple").
        npc_slug: slug name (e.g. "npc_maple").
        attribute: it can be 'strength', 'decay_rate' or 'decay_threshold'
        value: the new value
    """

    name = "modify_contacts"
    character: str
    npc_slug: str
    attribute: str
    value: float

    def start(self, session: Session) -> None:
        character = get_npc(session, self.character)
        if character is None:
            logger.error(f"{self.character} not found")
            return

        relationships = character.relationships
        contact = relationships.get_connection(self.npc_slug)

        if contact is None:
            logger.error(f"{self.npc_slug} already exist")
            return

        if self.attribute == "decay_rate":
            relationships.update_connection_decay_rate(
                self.npc_slug, self.value
            )
        elif self.attribute == "decay_threshold":
            relationships.update_connection_decay_threshold(
                self.npc_slug, int(self.value)
            )
        elif self.attribute == "strength":
            relationships.update_connection_strength(
                self.npc_slug, int(self.value)
            )
        else:
            logger.error(
                f"{self.attribute} must be 'strength', 'decay_rate' or 'decay_threshold'"
            )
            return
