# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session

logger = logging.getLogger(__name__)

BUTTON_NAME_TO_ID = {
    "HOME": 0,
    "UP": 1,
    "DOWN": 2,
    "LEFT": 4,
    "RIGHT": 8,
    "SELECT": 16,
    "START": 32,
    "A": 64,
    "B": 128,
    "X": 256,
    "Y": 512,
    "R1": 1024,
    "L1": 2048,
    "R2": 4096,
    "L2": 8192,
    "BACK": 16384,
    "MOUSELEFT": 32768,
}
BUTTON_NAME_TO_ID = {k.upper(): v for k, v in BUTTON_NAME_TO_ID.items()}
BUTTON_ID_TO_NAME = {v: k for k, v in BUTTON_NAME_TO_ID.items()}


@final
@dataclass
class RemoveComboAction(EventAction):
    """
    Removes a registered combo sequence from the ComboDetector.

    Script usage:
        .. code-block::

            remove_combo  <combo_name>[,buttons]

    Script parameters:
        combo_name: Required. A name or ID for the combo (used for logging).
        buttons: Required. A colon-separated list of button names (e.g. LEFT:RIGHT:A).
    """

    name = "remove_combo"
    combo_name: str
    values: str

    def start(self, session: Session) -> None:
        try:
            button_names = self.values.split(":")
            button_sequence = [
                BUTTON_NAME_TO_ID[name.strip().upper()]
                for name in button_names
            ]
            if not button_sequence:
                logger.warning(f"Combo '{self.combo_name}' has no buttons.")
                self.stop()
                return
        except KeyError as e:
            logger.warning(f"Unknown button name in combo: {e}")
            self.stop()
            return
        except Exception as e:
            logger.warning(f"Invalid combo definition: {self.values} — {e}")
            self.stop()
            return

        try:
            removed = session.client.input_manager.combo_manager.detector.remove_combo(
                button_sequence
            )
            named_sequence = [
                BUTTON_ID_TO_NAME.get(b, str(b)) for b in button_sequence
            ]
            if removed:
                logger.debug(
                    f"Combo '{self.combo_name}' removed: {named_sequence}"
                )
            else:
                logger.warning(
                    f"Combo '{self.combo_name}' not found: {named_sequence}"
                )
        except Exception as e:
            logger.warning(f"Failed to remove combo: {type(e).__name__}: {e}")
