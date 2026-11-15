# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, final

from tuxemon.constants.paths import mods_folder
from tuxemon.database.yaml_utils import load_yaml
from tuxemon.event.eventaction import EventAction
from tuxemon.platform.combo_detector import ComboProfile
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
    Registers one or more combos from a YAML string.

    Script usage:
        .. code-block::

            add_combo <yaml_data>

    Script parameters:
        yaml_file: Name of the YAML file (without extension) located in the mods folder.
    """

    name = "add_combo"
    yaml_data: str | None = None

    def start(self, session: Session) -> None:
        yaml_file = self.yaml_data or "combos"
        path = mods_folder / f"{yaml_file}.yaml"
        try:
            data = load_yaml(path)
            self._register_combos_from_yaml(data, session)
        except Exception as e:
            logger.warning(f"Failed to load combo YAML from '{path}': {e}")

    def _register_combos_from_yaml(self, data: Any, session: Session) -> None:
        for combo in data.get("combos", []):
            try:
                button_sequence = [
                    BUTTON_NAME_TO_ID[name.strip().upper()]
                    for name in combo["buttons"]
                ]
                if not button_sequence:
                    logger.warning(
                        f"Combo '{combo.get('name', '?')}' has no buttons."
                    )
                    continue

                max_delay_s = float(combo.get("max_delay_s", 1.0))
                delays_s = [max_delay_s] * len(button_sequence)

                def make_callback(
                    event_name: str | None,
                    combo_name: str,
                ) -> Callable[[], None]:
                    def callback() -> None:
                        logger.info(f"Combo '{combo_name}' triggered!")
                        if event_name:
                            session.client.event_engine.execute_action(
                                "call_event", [event_name]
                            )

                    return callback

                profile = ComboProfile(
                    name=combo["name"],
                    buttons=button_sequence,
                    callback=make_callback(
                        combo.get("event_name"), combo["name"]
                    ),
                    delays_s=delays_s,
                    description=combo.get(
                        "description",
                        f"YAML-defined combo for {combo['name']}",
                    ),
                    character=combo.get("character"),
                    difficulty=int(combo.get("difficulty", 1)),
                    priority=int(combo.get("priority", 0)),
                    trigger_on_release=bool(
                        combo.get("trigger_on_release", False)
                    ),
                )

                session.client.input_manager.combo_manager.detector.add_combo(
                    profile
                )
                named_sequence = [
                    BUTTON_ID_TO_NAME.get(b, str(b)) for b in button_sequence
                ]
                logger.debug(
                    f"Combo '{combo['name']}' registered: {named_sequence}"
                )
            except Exception as e:
                logger.warning(
                    f"Failed to register combo '{combo.get('name', '?')}': {e}"
                )
