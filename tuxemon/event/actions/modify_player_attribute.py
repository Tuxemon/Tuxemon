# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.event.actions.common import CommonAction
from tuxemon.event.eventaction import EventAction


@final
@dataclass
class ModifyPlayerAttributeAction(
    EventAction,
):
    """
    Modify the given attribute of the player character by modifier.

    By default this is achieved via addition, but prepending a '%' will cause
    it to be multiplied by the attribute.

    Script usage:
        .. code-block::

            modify_player_attribute <attribute>,<value>

    Script parameters:
        attribute: Name of the attribute to modify.
        value: Value of the attribute modifier.

    """

    name = "modify_player_attribute"
    attribute: str
    value: str

    def start(self) -> None:
        CommonAction.modify_character_attribute(
            self.session.player,
            self.attribute,
            self.value,
        )
