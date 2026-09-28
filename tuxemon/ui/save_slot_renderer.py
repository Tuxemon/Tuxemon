# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from base64 import b64decode
from typing import TYPE_CHECKING

from pygame import SRCALPHA
from pygame.image import frombuffer
from pygame.surface import Surface
from pygame.transform import smoothscale

from tuxemon.locale.locale import T
from tuxemon.platform.const.graphics import WHITE_COLOR
from tuxemon.ui.text import draw_text

if TYPE_CHECKING:
    from pygame.font import Font
    from pygame.rect import Rect

    from tuxemon.save_system.save_state import SaveData
    from tuxemon.scaling import ScalingStrategy


def render_thumbnail(save_data: SaveData, rect: Rect) -> Surface:
    """Return a scaled thumbnail or fallback placeholder."""
    if (
        save_data.screenshot
        and save_data.screenshot_width
        and save_data.screenshot_height
    ):
        raw = b64decode(save_data.screenshot)
        size = (save_data.screenshot_width, save_data.screenshot_height)
        img = frombuffer(raw, size, "RGB").convert()
        thumb_rect = img.get_rect().fit(rect)
        return smoothscale(img, thumb_rect.size)

    # fallback
    thumb_rect = rect.copy()
    thumb_rect.width //= 5
    img = Surface(thumb_rect.size)
    img.fill(WHITE_COLOR)
    return img


def render_empty_slot(
    rect: Rect, scaling: ScalingStrategy, font: Font, slot: int
) -> Surface:
    """Render the 'empty slot' UI block."""
    slot_image = Surface(rect.size, SRCALPHA)
    text_rect = rect.move(0, rect.height // 2 - 10)

    label = (
        T.translate("menu_no_autosave")
        if slot == 0
        else T.translate("empty_slot")
    )

    draw_text(
        slot_image,
        label,
        text_rect,
        scaling=scaling,
        font=font,
    )
    return slot_image


def render_slot_text(
    slot_image: Surface,
    rect: Rect,
    slot_label: str,
    save_data: SaveData,
    scaling: ScalingStrategy,
    font: Font,
) -> None:
    """Draw slot number, player name, and time."""
    draw_text(
        slot_image,
        slot_label,
        rect,
        scaling=scaling,
        font=font,
    )

    x = int(rect.width * 0.5)

    if save_data.npc_state and save_data.npc_state.player_name:
        draw_text(
            slot_image,
            save_data.npc_state.player_name,
            (x, 0, 500, 500),
            scaling=scaling,
            font=font,
        )

    if save_data.time:
        draw_text(
            slot_image,
            save_data.time,
            (x, 50, 500, 500),
            scaling=scaling,
            font=font,
        )
