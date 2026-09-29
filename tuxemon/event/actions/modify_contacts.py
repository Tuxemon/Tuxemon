# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

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
        character = session.client.get_npc(self.character)
        if character is None:
            logger.error(f"{self.character} not found")
            self.stop()
            return

        contact = character.relationships.get_connection(self.npc_slug)
        if contact is None:
            logger.error(f"Contact '{self.npc_slug}' does not exist")
            self.stop()
            return

        session.client.event_bus.publish(
            "relationship_modified",
            npc_slug=self.npc_slug,
            attribute=self.attribute,
            value=self.value,
        )
