# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Union, final

from tuxemon import prepare
from tuxemon.event.eventaction import EventAction
from tuxemon.locale import T
from tuxemon.menu.input import InputMenu

logger = logging.getLogger(__name__)


@final
@dataclass
class RenamePlayerAction(EventAction):
    """
    Open the text input screen to rename the player.

    Script usage:
        .. code-block::

            rename_player [random]

    Script parameters:
        random: Adding "random" makes appear the
        dontcare button in the input.

    """

    name = "rename_player"
    random: Union[str, None] = None

    def set_player_name(self, name: str) -> None:
        player = self.session.player
        logger.info(f"{player.name} has been changed into {name}")
        player.name = name

    def start(self) -> None:
        self.session.client.push_state(
            InputMenu(
                prompt=T.translate("input_name"),
                callback=self.set_player_name,
                escape_key_exits=False,
                initial=self.session.player.name,
                char_limit=prepare.PLAYER_NAME_LIMIT,
                random=bool(self.random),
            )
        )

    def update(self) -> None:
        try:
            self.session.client.get_state_by_name(InputMenu)
        except ValueError:
            self.stop()
