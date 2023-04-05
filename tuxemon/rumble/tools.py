# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from typing import List, Optional

try:
    from ctypes import cdll
except:
    cdll = None


class Rumble:
    def __init__(self) -> None:
        pass

    def rumble(
        self,
        target: float = 0,
        period: float = 25,
        magnitude: float = 24576,
        length: float = 2,
        delay: float = 0,
        attack_length: float = 256,
        attack_level: float = 0,
        fade_length: float = 256,
        fade_level: float = 0,
        direction: float = 16384,
    ) -> None:
        pass


def find_library(locations: List[str]) -> Optional[str]:
    for path in locations:
        try:
            lib = cdll.LoadLibrary(path)
            library = path
        except OSError as e:
            lib_shake = None
            library = None
        if library:
            return library

    return None
