# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from enum import Enum, auto

logger = logging.getLogger(__name__)


class MenuState(Enum):
    CLOSED = auto()
    OPENING = auto()
    NORMAL = auto()
    DISABLED = auto()
    CLOSING = auto()


class MenuController:
    """
    Controls the state transitions for a menu.

    Safely manages state without raising exceptions. Unexpected transitions are logged.
    """

    def __init__(self) -> None:
        self._state = MenuState.CLOSED

    @property
    def state(self) -> MenuState:
        return self._state

    def open(self) -> None:
        if self._state == MenuState.CLOSED:
            self._state = MenuState.OPENING
            logger.debug("MenuController: transitioned to OPENING")
        elif self._state == MenuState.OPENING:
            logger.debug("MenuController: already opening")
        elif self._state == MenuState.NORMAL:
            logger.debug(
                "MenuController: already open (NORMAL); open() skipped."
            )
        else:
            logger.warning(
                f"MenuController.open() called from {self._state.name}; ignored."
            )

    def set_normal(self) -> None:
        if self._state in {MenuState.OPENING, MenuState.DISABLED}:
            self._state = MenuState.NORMAL
            logger.debug("MenuController: transitioned to NORMAL")
        elif self._state == MenuState.NORMAL:
            logger.debug(
                "MenuController: already in NORMAL; set_normal() skipped."
            )
        else:
            logger.warning(
                f"MenuController.set_normal() called from {self._state.name}; ignored."
            )

    def disable(self) -> None:
        if self._state == MenuState.NORMAL:
            self._state = MenuState.DISABLED
            logger.debug("MenuController: transitioned to DISABLED")
        elif self._state == MenuState.DISABLED:
            logger.debug("MenuController: already disabled")
        else:
            logger.warning(
                f"MenuController.disable() called from {self._state.name}; ignored."
            )

    def enable(self) -> None:
        if self._state == MenuState.DISABLED:
            self._state = MenuState.NORMAL
            logger.debug("MenuController: transitioned to NORMAL (enabled)")
        elif self._state == MenuState.NORMAL:
            logger.debug("MenuController: already enabled")
        else:
            logger.warning(
                f"MenuController.enable() called from {self._state.name}; ignored."
            )

    def close(self) -> None:
        if self._state in {MenuState.NORMAL, MenuState.DISABLED}:
            self._state = MenuState.CLOSING
            logger.debug("MenuController: transitioned to CLOSING")
        elif self._state == MenuState.CLOSING:
            logger.debug("MenuController: already closing")
        else:
            logger.warning(
                f"MenuController.close() called from {self._state.name}; ignored."
            )

    def reset(self) -> None:
        self._state = MenuState.CLOSED
        logger.debug("MenuController: forcibly reset to CLOSED")

    def is_enabled(self) -> bool:
        return self._state == MenuState.NORMAL

    def is_closed(self) -> bool:
        return self._state == MenuState.CLOSED

    def is_disabled(self) -> bool:
        return self._state == MenuState.DISABLED

    def is_interactive(self) -> bool:
        return self._state in {MenuState.NORMAL, MenuState.OPENING}
