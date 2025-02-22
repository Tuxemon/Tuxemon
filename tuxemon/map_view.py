# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import os
from collections.abc import Mapping
from typing import TYPE_CHECKING, Union

import pygame

from tuxemon import prepare, surfanim
from tuxemon.db import EntityFacing
from tuxemon.graphics import load_and_scale
from tuxemon.surfanim import SurfaceAnimation

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tuxemon.npc import NPC

SpriteMap = Union[
    Mapping[str, pygame.surface.Surface],
    Mapping[str, SurfaceAnimation],
]


class SpriteRenderer:
    """A class for rendering sprites."""
    animation_mapping = {
        "walking": {
            "up": "back_walk",
            "down": "front_walk",
            "left": "left_walk",
            "right": "right_walk",
        },
        "idle": {
            "up": "back",
            "down": "front",
            "left": "left",
            "right": "right",
        },
    }

    def __init__(self, npc: NPC) -> None:
        self.npc = npc
        self.standing: dict[str, pygame.surface.Surface] = {}
        self.sprite: dict[str, surfanim.SurfaceAnimation] = {}
        self.surface_animations = surfanim.SurfaceAnimationCollection()
        self.playerWidth = 0
        self.playerHeight = 0
        self.rect = pygame.rect.Rect(0, 0, 0, 0)
        self.load_sprites()

    def load_sprites(self) -> None:
        """Load sprite graphics."""
        self.interactive_obj: bool = False
        if self.npc.template.slug == "interactive_obj":
            self.interactive_obj = True

        self.standing = {}
        for standing_type in list(EntityFacing):
            if self.interactive_obj:
                filename = f"{self.npc.template.sprite_name}.png"
                path = os.path.join("sprites_obj", filename)
            else:
                filename = f"{self.npc.template.sprite_name}_{standing_type.value}.png"
                path = os.path.join("sprites", filename)
            self.standing[standing_type] = load_and_scale(path)

        self.playerWidth, self.playerHeight = self.standing[
            EntityFacing.front
        ].get_size()

        n_frames = 3
        frame_duration = (
            (1000 / prepare.CONFIG.player_walkrate) / n_frames / 1000 * 2
        )

        anim_types = list(EntityFacing)
        for anim_type in anim_types:
            if not self.interactive_obj:
                images: list[str] = []
                anim_0 = f"sprites/{self.npc.template.sprite_name}_{anim_type.value}_walk"
                anim_1 = f"sprites/{self.npc.template.sprite_name}_{anim_type.value}.png"
                images.append(f"{anim_0}.{str(0).zfill(3)}.png")
                images.append(anim_1)
                images.append(f"{anim_0}.{str(1).zfill(3)}.png")
                images.append(anim_1)

                frames: list[tuple[pygame.surface.Surface, float]] = []
                for image in images:
                    surface = load_and_scale(image)
                    frames.append((surface, frame_duration))

                _surfanim = surfanim.SurfaceAnimation(frames, loop=True)
                self.sprite[f"{anim_type.value}_walk"] = _surfanim

        self.surface_animations.add(self.sprite)
        self.rect = pygame.rect.Rect(
            (
                self.npc.tile_pos[0],
                self.npc.tile_pos[1],
                self.playerWidth,
                self.playerHeight,
            )
        )

    def update(self, time_delta: float) -> None:
        """Update the sprite animation."""
        self.surface_animations.update(time_delta)
        self.rect.topleft = self.npc.tile_pos

    def get_frame(self, ani: str) -> pygame.surface.Surface:
        """Get the current frame of the sprite animation."""
        frame_dict: SpriteMap = (
            self.sprite if self.npc.moving else self.standing
        )
        frame = frame_dict[ani]
        if isinstance(frame, SurfaceAnimation):
            surface = frame.get_current_frame()
            frame.rate = self.npc.moverate / prepare.CONFIG.player_walkrate
            return surface
        else:
            return frame
