# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.locale import T
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class AddContactsAction(EventAction):
    """
    Add contact to the app.
    npc_slug must have the msgid inside the PO.

    Script usage:
        .. code-block::

            add_contacts <character>,<npc_slug>[,relation][,strength],
                        [,steps][,decay_rate][,decay_threshold]

    Script parameters:
        character: Either "player" or character slug name (e.g. "npc_maple").
        npc_slug: slug name (e.g. "npc_maple").
        relation: type of relation
        strength: amount of strength (higher, better), default 50, capped 100
        steps: amount of steps, default character steps
        decay_rate: decay rate of the relationship, default 0.01, capped 1.0
        decay_threshold: threshold of steps after which the decay triggers,
            default 500
    """

    name = "add_contacts"
    character: str
    npc_slug: str
    relation: Optional[str] = None
    strength: Optional[int] = None
    steps: Optional[float] = None
    decay_rate: Optional[float] = None
    decay_threshold: Optional[int] = None

    def start(self, session: Session) -> None:
        character = get_npc(session, self.character)
        if character is None:
            logger.error(f"{self.character} not found")
            return

        if self.relation is not None:
            if not T.has_translation(
                "en_US", f"relation_{self.relation.lower()}"
            ):
                logger.error(
                    f"Add msgid 'relation_{self.relation}' in the 'en_US' base.po"
                )
                return

        if self.strength is not None:
            self.strength = max(0, min(self.strength, 100))
        if self.decay_rate is not None:
            self.decay_rate = max(0.0, min(self.decay_rate, 1.0))

        relationships = character.relationships
        contact = relationships.get_connection(self.npc_slug)
        if contact is None:
            relationships.add_connection(
                slug=self.npc_slug,
                relationship_type=self.relation or "unknown",
                strength=self.strength or 50,
                steps=self.steps or character.steps,
                decay_rate=self.decay_rate or 0.01,
                decay_threshold=self.decay_threshold or 500,
            )
        else:
            contact.apply_decay(character)
            logger.error(f"{self.npc_slug} already exist")
            return
