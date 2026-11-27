# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""Autosave whenever the player arrives on a new map."""

from __future__ import annotations

import logging
from collections.abc import Callable

logger = logging.getLogger(__name__)


class MapAutosave:
    """
    Saves to the autosave slot once per map change.

    The map the game starts or loads on does not count as a change. After a
    change, the save waits until saving has been safe (no cutscene, menu,
    fade or walking in progress) for ``settle`` seconds in a row, so a map
    change in the middle of a scripted scene saves only once the scene has
    finished, not in the one-frame gap between two of its events.

    Parameters:
        save: Writes the autosave.
        settle: Seconds saving must stay safe before it happens.
    """

    def __init__(self, save: Callable[[], None], settle: float = 0.0) -> None:
        self._save = save
        self._settle = settle
        self._map: str | None = None
        self._pending = False
        self._safe_for = 0.0

    @property
    def pending(self) -> bool:
        return self._pending

    def update(self, map_name: str, can_save: bool, dt: float = 0.0) -> bool:
        """
        Call every world update. Returns True if it saved.

        Parameters:
            map_name: Name of the map the player is on now.
            can_save: Whether saving is safe this frame.
            dt: Seconds since the last update.
        """
        if not map_name:
            return False
        if self._map is None:
            self._map = map_name
            return False
        if map_name != self._map:
            self._map = map_name
            self._pending = True
        if not (self._pending and can_save):
            self._safe_for = 0.0
            return False
        self._safe_for += dt
        if self._safe_for < self._settle:
            return False
        self._pending = False
        self._safe_for = 0.0
        try:
            self._save()
        except Exception as e:
            logger.error(f"Map autosave failed: {e}")
            return False
        logger.info(f"Autosaved on arriving at {map_name}.")
        return True
