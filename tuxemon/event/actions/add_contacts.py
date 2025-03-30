# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction


@final
@dataclass
class AddContactsAction(EventAction):
    """
    Add contact to the app.

    slug must have the msgid inside the PO.

    Script usage:
        .. code-block::

            add_contacts <slug>,<phone_number>

    Script parameters:
        slug: slug name (e.g. "npc_maple").
        phone_number: 3 digits

    """

    name = "add_contacts"
    slug: str
    phone_number: str

    def start(self) -> None:
        player = self.session.player.contacts
        contact = self.slug
        phone = self.phone_number

        if len(phone) == 3:
            if contact not in player:
                player[str(contact)] = phone
            else:
                return
        else:
            raise ValueError(
                f"{phone} must be 3 digits.",
            )
