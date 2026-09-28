# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.computer import PCMenuBuilder, PCMenuRegistry
from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session

logger = logging.getLogger()


@final
@dataclass
class AccessPCAction(EventAction):
    """
    Open a PC interface for a specific character.

    This action transitions the game into ``PCState`` and displays a
    context-appropriate PC menu. The menu contents are determined by:

      • The target character (NPC) being viewed
      • The ``pc_tags`` string provided in the script
      • Any registered ``MenuProvider`` objects whose tags match

    ``pc_tags`` is a colon-separated list of tag identifiers.
    Example:
        ``standard:email:league``

    This allows maps, story events, and mods to define complex PC
    terminals that combine multiple feature sets—for example:
    a standard PC with email access, a league PC with storage, or
    any custom combination added by extensions.

    Script usage:
        .. code-block::

            access_pc <character_slug> [pc_tags]

    Script parameters:
        character_slug:
            The slug of the NPC whose PC interface should be opened.
        pc_tags (optional):
            A colon-separated string of PC tags.
            Defaults to ``"standard"`` if omitted.
            Each tag enables additional menu providers from
            ``PCMenuRegistry``.
    """

    name = "access_pc"
    character_slug: str
    pc_tags: str = "standard"

    def start(self, session: Session) -> None:
        self.session = session
        self.client = session.client

        character = self.session.client.get_npc(self.character_slug)
        if not character:
            self.stop()
            return

        tag_list = [
            tag.strip() for tag in self.pc_tags.split(":") if tag.strip()
        ]

        providers = []
        for tag in tag_list:
            providers.extend(PCMenuRegistry.get_for_tag(tag))

        menu_builder = PCMenuBuilder(
            client=self.client,
            character=character,
            menu_providers=providers,
            tag_list=tag_list,
        )

        self.client.push_state(
            "PCState",
            character=character,
            tag_list=tag_list,
            menu_builder=menu_builder,
        )

    def update(self, session: Session, dt: float) -> None:
        if "PCState" not in session.client.active_state_names:
            self.stop()
