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
class ChangeFactionMembershipAction(EventAction):
    """
    Makes an NPC (or player) join or leave a specific faction.

    Script usage:
        .. code-block::

            change_faction_membership <character>,<faction_slug>,<status>

    Script parameters:
        character: Either "player" or npc slug name (e.g. "npc_maple").
        faction_slug: The slug identifier of the faction whose membership will be changed.
        status: Must be either "join" or "leave", indicating the membership action.
    """

    name = "change_faction_membership"
    character: str
    faction_slug: str
    status: str

    def start(self, session: Session) -> None:
        if self.status not in {"join", "leave"}:
            raise ValueError(f"{self.status} must be 'join' or 'leave'")

        char = session.client.get_npc(self.character)
        if not char:
            logger.error(f"[Membership] NPC '{self.character}' not found.")
            self.stop()
            return

        faction_manager = session.world.faction_manager
        faction = faction_manager.get(self.faction_slug)
        if not faction:
            logger.error(
                f"[Membership] Faction '{self.faction_slug}' not found."
            )
            self.stop()
            return

        if self.status == "join":
            if not faction.has_member(char.slug):
                faction.add_member(char.slug)
                logger.info(
                    f"[Membership] {char.slug} joined {self.faction_slug}."
                )
            else:
                logger.debug(
                    f"[Membership] {char.slug} already in {self.faction_slug}."
                )
        elif self.status == "leave":
            if faction.has_member(char.slug):
                faction.remove_member(char.slug)
                logger.info(
                    f"[Membership] {char.slug} left {self.faction_slug}."
                )
            else:
                logger.debug(
                    f"[Membership] {char.slug} not in {self.faction_slug}."
                )

        faction_manager.clear_membership_cache(char.slug)
