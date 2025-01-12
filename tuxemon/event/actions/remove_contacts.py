# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction


@final
@dataclass
class RemoveContactsAction(EventAction):
    """
    Remove contact from the app.

    Script usage:
        .. code-block::

            remove_contacts <slug>

    Script parameters:
        slug: slug name (e.g. "npc_maple").

    """

    name = "remove_contacts"
    slug: str

    def start(self) -> None:
        player = self.session.player
        contact = self.slug

        if contact in player.contacts:
            player.contacts.pop(contact)
        else:
            return
