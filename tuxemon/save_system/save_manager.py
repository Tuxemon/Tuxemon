# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from pygame import SRCALPHA
from pygame.font import Font
from pygame.rect import Rect
from pygame.surface import Surface

from tuxemon.locale.locale import T
from tuxemon.save_system import save
from tuxemon.save_system.save import get_save_path
from tuxemon.save_system.save_slots import AUTOSAVE_SLOT, ui_to_save_index
from tuxemon.ui.save_slot_renderer import (
    render_empty_slot,
    render_slot_text,
    render_thumbnail,
)

if TYPE_CHECKING:
    from tuxemon.save_system.save_state import SaveData
    from tuxemon.scaling import ScalingStrategy
    from tuxemon.session import Session

logger = logging.getLogger(__name__)


class SaveManager:
    @staticmethod
    def exists(slot: int) -> bool:
        return Path(get_save_path(slot)).exists()

    @staticmethod
    def load(slot: int) -> SaveData | None:
        return save.load(get_save_path(slot))

    @staticmethod
    def delete(slot: int) -> bool:
        path = Path(get_save_path(slot))
        if not path.exists():
            logger.warning(f"Save slot {slot} does not exist.")
            return False
        try:
            path.unlink()
            logger.info(f"Deleted save slot {slot} at {path}.")
            return True
        except OSError as e:
            logger.error(f"Failed to delete save slot {slot}: {e}")
            return False

    @staticmethod
    def save(session: Session, slot: int) -> None:
        """
        Save both index and slot as the same number.
        This matches how save_state() is used in the engine.
        """
        session.save_state(index=slot, slot=slot)

    @staticmethod
    def has_autosave() -> bool:
        """Helper to specifically check for the autosave slot."""
        return SaveManager.exists(AUTOSAVE_SLOT)

    @staticmethod
    def all_slots(max_slots: int, include_autosave: bool = False) -> list[int]:
        slots = [ui_to_save_index(i) for i in range(max_slots)]
        return ([AUTOSAVE_SLOT] + slots) if include_autosave else slots

    @staticmethod
    def slot_from_ui(ui_index: int, includes_autosave: bool = False) -> int:
        return ui_index if includes_autosave else ui_to_save_index(ui_index)

    @staticmethod
    def render_empty(
        rect: Rect, slot: int, scaling: ScalingStrategy, font: Font
    ) -> Surface:
        return render_empty_slot(
            rect,
            scaling=scaling,
            font=font,
            slot=slot,
        )

    @staticmethod
    def render_slot(
        rect: Rect, slot: int, scaling: ScalingStrategy, font: Font
    ) -> Surface:
        slot_image = Surface(rect.size, SRCALPHA)
        save_data = SaveManager.load(slot)

        if not save_data:
            raise RuntimeError(f"Save data missing for slot {slot}")

        thumb = render_thumbnail(save_data, rect)
        slot_image.blit(thumb, (rect.width * 0.20, 0))

        slot_label = (
            T.translate("menu_autosave")
            if slot == AUTOSAVE_SLOT
            else f"{T.translate('slot')} {slot}"
        )

        text_rect = Rect(
            0, rect.height // 2 - 10, rect.width, rect.height // 2
        )

        render_slot_text(
            slot_image,
            text_rect,
            slot_label,
            save_data,
            scaling=scaling,
            font=font,
        )
        return slot_image
