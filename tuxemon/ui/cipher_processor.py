# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any, Optional

logger = logging.getLogger(__name__)


class CipherProcessor:
    """
    Applies a custom cipher to text, respecting unlocked letters.
    """

    def __init__(
        self,
        cipher_map: dict[str, str],
        unlocked_letters: Optional[set[str]] = None,
    ) -> None:
        self._unlocked_letters = unlocked_letters or set()
        self._cipher_map = cipher_map
        self._lower_cipher_map = {
            k.lower(): v.lower() for k, v in self._cipher_map.items()
        }

    def set_unlocked_letters(self, letters: set[str]) -> None:
        self._unlocked_letters = letters or set()

    def set_cipher_map(self, cipher_map: dict[str, str]) -> None:
        self._cipher_map = cipher_map
        self._lower_cipher_map = {
            k.lower(): v.lower() for k, v in self._cipher_map.items()
        }

    def apply_cipher(self, text: str) -> str:
        unlocked = self._unlocked_letters
        result = []

        for char in text:
            upper = char.upper()
            if upper in self._cipher_map:
                if upper in unlocked:
                    result.append(char)
                else:
                    result.append(
                        self._cipher_map[upper]
                        if char.isupper()
                        else self._lower_cipher_map[char]
                    )
            else:
                result.append(char)

        return "".join(result)


def encode_cipher(unlocked_letters: set[str]) -> Mapping[str, Any]:
    return {"unlocked_letters": list(unlocked_letters)}


def decode_cipher(save_data: Mapping[str, Any]) -> set[str]:
    try:
        letters = save_data.get("unlocked_letters", [])
        return {
            str(letter).upper()
            for letter in letters
            if isinstance(letter, str)
            and len(letter) == 1
            and letter.isalpha()
        }
    except Exception as e:
        logger.warning(f"Could not load cipher letters for NPC: {e}")
        return set()
