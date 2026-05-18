# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from pygame import BLEND_RGBA_MULT

from tuxemon.graphics import ColorLike
from tuxemon.map.view import load_and_scale_with_cache

if TYPE_CHECKING:
    from pygame.surface import Surface

    from tuxemon.db import NpcTemplateModel
    from tuxemon.entity.npc import NPC


@dataclass
class RuntimeAppearance:
    sprite_name: str
    combat_sheet: str
    outfit: str | None = None
    accessory: str | None = None
    palette: str | None = None
    color: ColorLike | None = None

    combat_frame_width: int | None = None
    combat_frame_height: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "sprite_name": self.sprite_name,
            "combat_sheet": self.combat_sheet,
            "outfit": self.outfit,
            "accessory": self.accessory,
            "palette": self.palette,
            "color": self.color,
            "combat_frame_width": self.combat_frame_width,
            "combat_frame_height": self.combat_frame_height,
        }

    @classmethod
    def from_template(cls, template: NpcTemplateModel) -> RuntimeAppearance:
        return cls(
            sprite_name=template.sprite_name,
            combat_sheet=template.combat_sheet,
            combat_frame_width=template.combat_frame_width,
            combat_frame_height=template.combat_frame_height,
        )

    @classmethod
    def from_dict(
        cls, data: dict[str, Any], template: NpcTemplateModel
    ) -> RuntimeAppearance:
        return cls(
            sprite_name=data.get("sprite_name", template.sprite_name),
            combat_sheet=data.get("combat_sheet", template.combat_sheet),
            outfit=data.get("outfit"),
            accessory=data.get("accessory"),
            palette=data.get("palette"),
            color=data.get("color"),
            combat_frame_width=data.get(
                "combat_frame_width", template.combat_frame_width
            ),
            combat_frame_height=data.get(
                "combat_frame_height", template.combat_frame_height
            ),
        )


class AppearanceManager:
    """
    Handles changing and persisting the visual state of an NPC.
    """

    DEFAULT_RACE_MAPPING = {
        "gender_enby": ("enbyasian", "enbyasian"),
        "gender_whatever": ("penguin", "penguin"),
        "black_female": ("brownheroine_brown", "heroineblack"),
        "black_male": ("adventurerblack", "adventurerblack"),
        "white_female": ("heroine", "heroine"),
        "white_male": ("adventurer", "adventurer"),
    }

    def __init__(self, owner: NPC):
        self.owner = owner
        self.state = RuntimeAppearance.from_template(owner.template)

    def update(
        self, sprite_name: str, combat_sheet: str | None = None
    ) -> None:
        self.state.sprite_name = sprite_name
        if combat_sheet is not None:
            self.state.combat_sheet = combat_sheet

        self.owner.sprite_controller.update_appearance(self.state)

    def update_layers(
        self,
        outfit: str | None = None,
        accessory: str | None = None,
        palette: str | None = None,
    ) -> None:
        if outfit is not None:
            self.state.outfit = outfit

        if accessory is not None:
            self.state.accessory = accessory

        if palette is not None:
            self.state.palette = palette

        self.owner.sprite_controller.update_appearance(self.state)

    def get_default_for_race(self, race: str) -> tuple[str | None, str | None]:
        return self.DEFAULT_RACE_MAPPING.get(race, (None, None))

    def reset_to_default(self) -> None:
        race = self.owner.game_variables.get("race_choice", "")
        sprite, sheet = self.get_default_for_race(race)

        if sprite and sheet:
            self.update(sprite, sheet)
            return

        template = self.owner.template
        self.state.sprite_name = template.sprite_name
        self.state.combat_sheet = template.combat_sheet

        self.owner.sprite_controller.update_appearance(self.state)

    def load_state(self, data: dict[str, Any]) -> None:
        new = RuntimeAppearance.from_dict(data, self.owner.template)

        self.state.sprite_name = new.sprite_name
        self.state.combat_sheet = new.combat_sheet
        self.state.outfit = new.outfit
        self.state.accessory = new.accessory
        self.state.palette = new.palette
        self.state.combat_frame_width = new.combat_frame_width
        self.state.combat_frame_height = new.combat_frame_height

        self.owner.sprite_controller.update_appearance(self.state)

    def build_composited_sheet(self) -> Surface:
        if self.owner.template.is_static_prop:
            base_path = f"sprites_obj/{self.state.sprite_name}.png"
        else:
            base_path = f"sprites/{self.state.sprite_name}.png"

        base = load_and_scale_with_cache(base_path)

        if self.state.color:
            tinted = base.copy()
            tinted.fill(self.state.color, special_flags=BLEND_RGBA_MULT)
            final = tinted
        else:
            final = base.copy()

        # Outfit
        if self.state.outfit:
            final.blit(
                load_and_scale_with_cache(f"sprites/{self.state.outfit}.png"),
                (0, 0),
            )

        # Accessory
        if self.state.accessory:
            final.blit(
                load_and_scale_with_cache(
                    f"sprites/{self.state.accessory}.png"
                ),
                (0, 0),
            )

        # Palette
        if self.state.palette:
            final.blit(
                load_and_scale_with_cache(f"sprites/{self.state.palette}.png"),
                (0, 0),
            )

        return final
