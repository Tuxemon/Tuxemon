# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, final

from tuxemon import save
from tuxemon.event.eventaction import EventAction
from tuxemon.locale import T
from tuxemon.tools import open_dialog

logger = logging.getLogger(__name__)


@final
@dataclass
class SaveGameAction(EventAction):
    """
    Saves the game.

    If the index parameter is absent, then it'll create
    slot4.save

    index = 0 > slot 1
    index = 1 > slot 2
    index = 2 > slot 3

    Script usage:
        .. code-block::

            save_game [index]

    Script parameters:
        index: Selected index.

    eg: "save_game" (slot4.save)
    eg: "save_game 1"

    """

    name = "save_game"
    index: Optional[int] = None

    def start(self) -> None:
        index = 4 if self.index is None else self.index + 1
        slot = 0 if self.index is None else self.index

        logger.info("Saving!")
        try:
            save_data = save.get_save_data(
                self.session,
            )
            save.save(
                save_data,
                index,
            )
            save.slot_number = slot
        except Exception as e:
            raise
            logger.error("Unable to save game!!")
            logger.error(e)
            open_dialog(self.session, [T.translate("save_failure")])
        else:
            if self.index is not None:
                open_dialog(self.session, [T.translate("save_success")])
            else:
                logger.info(T.translate("save_success"))
