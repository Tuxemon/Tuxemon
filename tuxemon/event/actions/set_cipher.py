# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, final

import yaml

from tuxemon.constants import paths
from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session
from tuxemon.ui.cipher_processor import CipherProcessor

logger = logging.getLogger(__name__)

DEFAULT_CIPHER_MAP = {
    "A": "K",
    "B": "X",
    "C": "S",
    "D": "Q",
    "E": "R",
    "F": "N",
    "G": "Y",
    "H": "O",
    "I": "V",
    "J": "Z",
    "K": "L",
    "L": "M",
    "M": "B",
    "N": "P",
    "O": "D",
    "P": "C",
    "Q": "U",
    "R": "F",
    "S": "J",
    "T": "H",
    "U": "G",
    "V": "A",
    "W": "E",
    "X": "T",
    "Y": "W",
    "Z": "I",
}


@final
@dataclass
class SetCipherAction(EventAction):
    """
    Toggles ciphering for dialogue by enabling or disabling the CipherProcessor.

    Script usage:
        .. code-block::
            set_cipher <option>,<cipher_map>

    Parameters:
        option:
        - "enable": Activates ciphering using the provided cipher map (if any).
        - "disable": Disables ciphering entirely.

        cipher_map: the filename (without extension) of a YAML file located in
            the mods folder.
        - If omitted during "enable", the default cipher map is used.
        - Ignored when option is "disable".
    """

    name = "set_cipher"
    option: Optional[str] = None
    cipher_map: Optional[str] = None

    def start(self, session: Session) -> None:
        if self.cipher_map:
            filename = self.cipher_map + ".yaml"
            yaml_path = paths.mods_folder / filename

            try:
                with yaml_path.open(encoding="utf-8") as f:
                    cipher_data = yaml.safe_load(f)
                    cipher_map = cipher_data.get("cipher_map")
                    if not cipher_map:
                        raise ValueError(
                            f"'cipher_map' key missing in {filename}"
                        )
            except Exception as e:
                logger.error(
                    f"Failed to load cipher map from {yaml_path}: {e}"
                )
                raise
        else:
            cipher_map = DEFAULT_CIPHER_MAP

        client = session.client
        if self.option == "enable":
            client.cipher_processor = CipherProcessor(cipher_map=cipher_map)
        elif self.option == "disable":
            client.cipher_processor = None
        else:
            raise ValueError(f"{self.option} must be 'enable' or 'disable'")
