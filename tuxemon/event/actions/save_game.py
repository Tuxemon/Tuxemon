# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.locale.locale import T
from tuxemon.save_system.save_manager import SaveManager
from tuxemon.save_system.save_slots import resolve_save_index
from tuxemon.session import Session
from tuxemon.tools import open_dialog

logger = logging.getLogger(__name__)


@final
@dataclass
class SaveGameAction(EventAction):
    """
    Saves the game to a specific save slot.

    The `index` parameter refers to the UI slot index (0-2).
    Slot resolution is handled by `resolve_save_index()`, which converts
    the UI index (0-based) into a save slot number (1-based).

    Script usage:
        .. code-block::

            save_game <index>

    Script parameters:
        index: UI slot index (0-2). Must always be provided.
    """

    name = "save_game"
    index: int

    def start(self, session: Session) -> None:
        slot = resolve_save_index(self.index)

        logger.info("Saving!")
        try:
            SaveManager.save(session, slot)
        except Exception as e:
            logger.error("Unable to save game!")
            logger.exception(e)
            open_dialog(
                session.client,
                [T.translate("save_failure")],
                dialog_speed="max",
            )
        else:
            open_dialog(
                session.client,
                [T.translate("save_success")],
                dialog_speed="max",
            )
