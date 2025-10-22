# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, final

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
class AddComboAction(EventAction):
    """
    Registers a new combo sequence with the ComboDetector.

    Script usage:
        .. code-block::

            add_combo  <combo_name>[,buttons][,max_delay_ms]

    Script parameters:
        combo_name: Required. A name or ID for the combo.
        buttons: Required. A colon-separated list of button names (e.g. LEFT:RIGHT:A).
        max_delay_ms: Optional. Max delay between presses (default: 1000).
        event_name: The name of the event whose actions will be executed (optional)
    """

    name = "add_combo"
    combo_name: str
    values: str
    event_name: Optional[str] = None

    def start(self, session: Session) -> None:
        try:
            parts = self.values.split(",")
            button_names = parts[0].split(":")
            button_sequence = [
                BUTTON_NAME_TO_ID[name.strip().upper()]
                for name in button_names
            ]
            if not button_sequence:
                logger.warning(f"Combo '{self.combo_name}' has no buttons.")
                return
            max_delay_ms = int(parts[1]) if len(parts) > 1 else 1000
        except KeyError as e:
            logger.warning(f"Unknown button name in combo: {e}")
            return
        except Exception as e:
            logger.warning(f"Invalid combo definition: {self.values} — {e}")
            return

        def on_combo_triggered() -> None:
            logger.info(f"Combo '{self.combo_name}' triggered!")
            if not self.event_name:
                return
            session.client.event_engine.execute_action(
                "call_event", [self.event_name]
            )

        try:
            session.client.input_manager.combo_manager.detector.add_combo(
                button_sequence, on_combo_triggered, max_delay_ms
            )
            named_sequence = [
                BUTTON_ID_TO_NAME.get(b, str(b)) for b in button_sequence
            ]
            logger.debug(
                f"Combo '{self.combo_name}' registered: {named_sequence}"
            )
        except Exception as e:
            logger.warning(
                f"Failed to register combo: {type(e).__name__}: {e}"
            )
