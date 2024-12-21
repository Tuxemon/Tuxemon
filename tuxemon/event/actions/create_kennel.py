# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction


@final
@dataclass
class CreateKennelAction(EventAction):
    """
    Creates a new kennel.

    It's advisable to create a msgid in the en_US PO file.

    msgid "kennel_name"
    msgstr "Kennel Name"

    Script usage:
        .. code-block::

            create_kennel <kennel>

    Script parameters:
        kennel: Name of the kennel.

    """

    name = "create_kennel"
    kennel: str

    def start(self) -> None:
        player = self.session.player
        if not player.monster_boxes.has_box(self.kennel, "monster"):
            player.monster_boxes.create_box(self.kennel, "monster")
