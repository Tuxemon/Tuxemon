# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging

from pygame import Rect

from tuxemon.database.runtime import db
from tuxemon.db import DialogueModel
from tuxemon.ui.text_alignment import DialogPosition
from tuxemon.user_config import CONFIG

logger = logging.getLogger(__name__)

LARGE_GUI_HEIGHT_RATIO = 0.4
SMALL_GUI_HEIGHT_RATIO = 0.25
SMALL_GUI_WIDTH_RATIO = 0.8


def scale_dialog_size(rect: Rect) -> Rect:
    """Scales the dialog size based on GUI configuration settings."""
    new = rect.copy()
    if CONFIG.large_gui:
        new.height = int(rect.height * LARGE_GUI_HEIGHT_RATIO)
    else:
        new.height = int(rect.height * SMALL_GUI_HEIGHT_RATIO)
        new.width = int(rect.width * SMALL_GUI_WIDTH_RATIO)
    return new


def resolve_reference_rect(
    screen_rect: Rect, target_coords: tuple[int, int] | Rect | None
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
    target_coords: tuple[int, int] | Rect | None = None,
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
    """

    def __init__(self) -> None:
        DialogueModel.load_cache(db)
        self._cache = DialogueModel.get_cache()

    def get(self, style_key: str) -> DialogueModel:
        """Retrieve the DialogueModel for the given style key from cache."""
        try:
            return self._cache[style_key]
        except KeyError:
            raise RuntimeError(f"Dialogue style '{style_key}' not found")

    def clear(self) -> None:
        """Clears the internal style cache."""
        self._cache.clear()

    def preload(self, keys: list[str]) -> None:
        """Preloads multiple styles into cache."""
        for key in keys:
            if key not in self._cache:
                try:
                    self._cache[key] = DialogueModel.lookup(key, db)
                except KeyError:
                    logger.warning(f"Failed to preload dialogue style '{key}'")
