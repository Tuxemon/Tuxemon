# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.event import get_npc
from tuxemon.event.actions.common import CommonAction
from tuxemon.event.eventaction import EventAction


@final
@dataclass
class SetNpcAttributeAction(EventAction):
    """
    Set the given attribute of the npc to the given value.

    Script usage:
        .. code-block::

            set_npc_attribute <npc_slug>,<attribute>,<value>

    Script parameters:
        npc_slug: Either "player" or npc slug name (e.g. "npc_maple").
        attribute: Name of the attribute.
        value: Value of the attribute.

    """

    name = "set_npc_attribute"
    npc_slug: str
    attribute: str
    value: str

    def start(self) -> None:
        npc = get_npc(self.session, self.npc_slug)
        assert npc
        CommonAction.set_character_attribute(npc, self.attribute, self.value)
