# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import Optional, Union

from pygame import Rect

from tuxemon import prepare
from tuxemon.db import DialogueModel, db
from tuxemon.ui.text_alignment import DialogPosition

logger = logging.getLogger(__name__)

LARGE_GUI_HEIGHT_RATIO = 0.4
SMALL_GUI_HEIGHT_RATIO = 0.25
SMALL_GUI_WIDTH_RATIO = 0.8


def scale_dialog_size(rect: Rect) -> Rect:
    """Scales the dialog size based on GUI configuration settings."""
    new = rect.copy()
    if prepare.CONFIG.large_gui:
        new.height = int(rect.height * LARGE_GUI_HEIGHT_RATIO)
    else:
        new.height = int(rect.height * SMALL_GUI_HEIGHT_RATIO)
        new.width = int(rect.width * SMALL_GUI_WIDTH_RATIO)
    return new


def resolve_reference_rect(
    screen_rect: Rect, target_coords: Optional[Union[tuple[int, int], Rect]]
) -> Rect:
    """Determines the reference rectangle based on target coordinates or defaults to the screen."""
    if target_coords is None:
        return screen_rect
    if isinstance(target_coords, Rect):
        return target_coords
    return Rect(target_coords[0], target_coords[1], 1, 1)


def calc_dialog_rect(
    screen_rect: Rect,
    position: DialogPosition,
    target_coords: Optional[Union[tuple[int, int], Rect]] = None,
) -> Rect:
    """
    Return a rect that is the area for a dialog box on the screen.

    Note:
        This only works with Pygame rects, as it modifies the attributes.

    Parameters:
        screen_rect: Rectangle of the screen.
        position: Position of the dialog box relative to the target_coords.
            Can be 'top', 'bottom', 'center', 'topleft', 'topright',
            'bottomleft', 'bottomright', 'right', 'left', or 'at_target'.
            If 'at_target', the dialog's topleft will be at target_coords.
        target_coords: Optional. A tuple (x, y) representing a point, or a Pygame Rect.
            If provided, the 'position' will be relative to this point/rect.
            If None, 'position' will be relative to screen_rect.

    Returns:
        Rectangle for a dialog.
    """
    rect = scale_dialog_size(screen_rect)
    reference_rect = resolve_reference_rect(screen_rect, target_coords)

    if position == DialogPosition.TOP:
        rect.top = reference_rect.top
        rect.centerx = reference_rect.centerx
    elif position == DialogPosition.BOTTOM:
        rect.bottom = reference_rect.bottom
        rect.centerx = reference_rect.centerx
    elif position == DialogPosition.CENTER:
        rect.center = reference_rect.center
    elif position == DialogPosition.TOPLEFT:
        rect.topleft = reference_rect.topleft
    elif position == DialogPosition.TOPRIGHT:
        rect.topright = reference_rect.topright
    elif position == DialogPosition.BOTTOMLEFT:
        rect.bottomleft = reference_rect.bottomleft
    elif position == DialogPosition.BOTTOMRIGHT:
        rect.bottomright = reference_rect.bottomright
    elif position == DialogPosition.LEFT:
        rect.left = reference_rect.left
        rect.centery = reference_rect.centery
    elif position == DialogPosition.RIGHT:
        rect.right = reference_rect.right
        rect.centery = reference_rect.centery
    elif position == DialogPosition.AT_TARGET:
        if not isinstance(target_coords, tuple):
            raise ValueError(
                "For 'at_target' position, target_coords must be a (x, y) tuple."
            )
        rect.topleft = target_coords
    else:
        raise ValueError(f"Invalid position: {position}")

    rect.clamp_ip(screen_rect)
    return rect


class DialogueStyleCache:
    """
    Handles lookup and caching of DialogueModel styles.

    Usage:
        style_cache = DialogueStyleCache()
        style = style_cache.get("default")
    """

    def __init__(self) -> None:
        self._cache: dict[str, DialogueModel] = {}

    def get(self, style_key: str) -> DialogueModel:
        """
        Retrieves a DialogueModel by key, caching the result.

        Raises:
            RuntimeError if style is not found in the DB.
        """
        if style_key in self._cache:
            return self._cache[style_key]

        try:
            style = DialogueModel.lookup(style_key, db)
            self._cache[style_key] = style
            return style
        except KeyError:
            logger.warning(f"Dialogue style '{style_key}' not found in DB.")
            raise RuntimeError(f"Dialogue style '{style_key}' not found")

    def clear(self) -> None:
        """Clears the internal style cache."""
        self._cache.clear()

    def preload(self, keys: list[str]) -> None:
        """Preloads multiple styles into cache, useful during scene setup."""
        for key in keys:
            if key not in self._cache:
                try:
                    self._cache[key] = DialogueModel.lookup(key, db)
                except KeyError:
                    logger.warning(f"Failed to preload dialogue style '{key}'")
