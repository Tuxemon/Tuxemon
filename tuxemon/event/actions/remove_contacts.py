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
class RemoveContactsAction(EventAction):
    """
    Remove contact from the app.

    Script usage:
        .. code-block::

            remove_contacts <character>,<slug>

    Script parameters:
        character: Either "player" or character slug name (e.g. "npc_maple").
        slug: slug name (e.g. "npc_maple").
    """

    name = "remove_contacts"
    character: str
    slug: str

    def start(self, session: Session) -> None:
        character = session.client.get_npc(self.character)
        if character is None:
            logger.error(f"{self.character} not found")
            self.stop()
            return

        relationships = character.relationships
        contact = relationships.get_connection(self.slug)
        if contact is None:
            logger.error("Nothing to remove")
            self.stop()
            return
        else:
            relationships.remove_connection(self.slug)
