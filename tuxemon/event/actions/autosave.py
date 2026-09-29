# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.save_system.save_manager import SaveManager
from tuxemon.save_system.save_slots import AUTOSAVE_SLOT
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class AutosaveAction(EventAction):
    """
    Performs an automatic save using the engine's autosave slot.

    This action triggers a write to the predefined `AUTOSAVE_SLOT`,
    which is managed internally by the save system. It requires no
    parameters and is typically invoked by scripted events that want
    to persist progress without user interaction.

    Script usage:
        .. code-block::

            autosave

    Script parameters:
        (none)
    """

    name = "autosave"

    def start(self, session: Session) -> None:
        try:
            SaveManager.save(session, AUTOSAVE_SLOT)
            logger.info("Autosave complete.")
        except Exception as e:
            logger.error(f"Autosave failed: {e}")
