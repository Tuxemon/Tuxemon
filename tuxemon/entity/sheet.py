# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from typing import TYPE_CHECKING

from tuxemon.graphics import load_raw_image

if TYPE_CHECKING:
    from pygame.surface import Surface

    from tuxemon.db import NpcTemplateModel


_COMBAT_SHEET_CACHE: dict[tuple[str, int, int, int | None], CombatSheet] = {}


def get_combat_sheet(template: NpcTemplateModel) -> CombatSheet:
    file = f"gfx/sprites/player/{template.combat_sheet}.png"

    key = (
        file,
        template.combat_frame_width,
        template.combat_frame_height,
        template.combat_back_frame_height,
    )

    if key not in _COMBAT_SHEET_CACHE:
        _COMBAT_SHEET_CACHE[key] = CombatSheet(
            file_path=file,
            frame_w=template.combat_frame_width,
            frame_h=template.combat_frame_height,
            back_frame_h=template.combat_back_frame_height,
        )

    return _COMBAT_SHEET_CACHE[key]


class CombatSheet:
    @classmethod
    def from_template(cls, template: NpcTemplateModel) -> CombatSheet:
        file = f"gfx/sprites/player/{template.combat_sheet}.png"
        return cls(
            file_path=file,
            frame_w=template.combat_frame_width,
            frame_h=template.combat_frame_height,
            back_frame_h=template.combat_back_frame_height,
        )

    def __init__(
        self,
        file_path: str,
        frame_w: int,
        frame_h: int,
        back_frame_h: int | None = None,
    ):
        self.file_path = file_path
        self.frame_w = frame_w
        self.frame_h = frame_h
        # When None, the back height is auto-detected from the sheet (it
        # fills the full image height). An explicit value is validated
        # against the image instead. This lets a taller back sprite be
        # dropped in by editing only the PNG, even when the combat sheet is
        # swapped at runtime (e.g. via race/appearance changes).
        self.back_frame_h = back_frame_h
        self.frames = self._slice()

    def _slice(self) -> dict[str, Surface]:
        sheet = load_raw_image(self.file_path)
        w, h = sheet.get_size()

        # The sheet is laid out back|front side-by-side. The back fills the
        # full image height while the front is top-aligned within its column
        # (any extra height below the front is transparent padding).
        back_h = self.back_frame_h if self.back_frame_h is not None else h
        expected_w = self.frame_w * 2
        expected_h = max(self.frame_h, back_h)

        if w != expected_w or h != expected_h:
            raise ValueError(
                f"Combat sheet '{self.file_path}' must be "
                f"{expected_w}x{expected_h}, but is {w}x{h}"
            )

        return {
            "back": sheet.subsurface((0, 0, self.frame_w, back_h)),
            "front": sheet.subsurface(
                (self.frame_w, 0, self.frame_w, self.frame_h)
            ),
        }

    def front(self) -> Surface:
        return self.frames["front"]

    def back(self) -> Surface:
        return self.frames["back"]
