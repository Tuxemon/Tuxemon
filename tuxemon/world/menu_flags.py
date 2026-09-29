# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class MenuFlags:
    """
    Stores and manages visibility states of world menu entries.
    Supports dynamic toggling, preset configurations, and export/import.
    """

    DEFAULT_PRESETS: dict[str, dict[str, bool]] = {
        "full": {
            "menu_bag": True,
            "menu_load": True,
            "menu_monster": True,
            "menu_save": True,
            "menu_player": True,
            "menu_missions": True,
        },
        "minimal": {
            "menu_bag": True,
            "menu_load": False,
            "menu_monster": True,
            "menu_save": False,
            "menu_player": True,
            "menu_missions": False,
        },
        "raw": {
            "menu_bag": False,
            "menu_load": True,
            "menu_monster": False,
            "menu_save": True,
            "menu_player": False,
            "menu_missions": False,
        },
    }

    def __init__(self, preset: str = "full") -> None:
        if preset not in self.DEFAULT_PRESETS:
            raise ValueError(f"Unknown preset: '{preset}'")
        self._flags: dict[str, bool] = self.DEFAULT_PRESETS[preset].copy()
        logger.debug(
            f"MenuFlags initialized with preset '{preset}' > {self._flags}"
        )

    def is_enabled(self, key: str) -> bool:
        result = self._flags.get(key, False)
        logger.debug(f"is_enabled('{key}') > {result}")
        return result

    def set_enabled(self, key: str, value: bool) -> None:
        if key not in self._flags:
            logger.debug(f"MenuFlags: auto-registering new menu key '{key}'")
        else:
            logger.debug(f"MenuFlags: updating '{key}' → {value}")
        self._flags[key] = value

    def reset_flags(self) -> None:
        for key in self._flags:
            self._flags[key] = False
        logger.debug("Resetting all menu flags: all visibility disabled")

    def enable(self, key: str) -> None:
        logger.debug(f"enable('{key}')")
        self.set_enabled(key, True)

    def disable(self, key: str) -> None:
        logger.debug(f"disable('{key}')")
        self.set_enabled(key, False)

    def apply_preset(self, preset: str) -> None:
        if preset not in self.DEFAULT_PRESETS:
            raise ValueError(f"Unknown preset: '{preset}'")
        logger.debug(f"apply_preset('{preset}')")
        self._flags = self.DEFAULT_PRESETS[preset].copy()

    def export(self) -> dict[str, bool]:
        logger.debug("export() called")
        return self._flags.copy()

    def import_flags(self, flags: dict[str, bool]) -> None:
        logger.debug(f"import_flags({flags})")
        for k in self._flags:
            if k in flags:
                self._flags[k] = bool(flags[k])
                logger.debug(f"> Imported '{k}' = {self._flags[k]}")
