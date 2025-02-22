# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import os
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
    dict[str, SurfaceAnimation], dict[str, pygame.surface.Surface]
]


class SpriteRenderer:
    """A class for rendering NPC sprites."""

    ANIMATION_MAPPING = {
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
        """Initialize the SpriteRenderer."""
        self.npc = npc
        self.standing: dict[
            Union[EntityFacing, str], pygame.surface.Surface
        ] = {}
        self.sprite: dict[str, SurfaceAnimation] = {}
        self.surface_animations = surfanim.SurfaceAnimationCollection()
        self.player_width = 0
        self.player_height = 0
        self.rect = pygame.rect.Rect(0, 0, 0, 0)
        self._load_sprites()

    def _load_sprites(self) -> None:
        """Load sprite graphics based on NPC type."""
        is_interactive_object = self.npc.template.slug == "interactive_obj"

        for facing in EntityFacing:
            filename = (
                f"{self.npc.template.sprite_name}.png"
                if is_interactive_object
                else f"{self.npc.template.sprite_name}_{facing.value}.png"
            )
            path = os.path.join(
                "sprites_obj" if is_interactive_object else "sprites", filename
            )
            self.standing[facing] = load_and_scale(path)

        self.player_width, self.player_height = self.standing[
            EntityFacing.front
        ].get_size()

        if not is_interactive_object:
            self._load_walking_animations()

        self.rect = pygame.rect.Rect(
            (
                self.npc.tile_pos[0],
                self.npc.tile_pos[1],
                self.player_width,
                self.player_height,
            )
        )

    def _load_walking_animations(self) -> None:
        """Load walking animation sprites."""
        frame_duration = self._calculate_frame_duration()

        for facing in EntityFacing:
            images: list[str] = []
            anim_0 = (
                f"sprites/{self.npc.template.sprite_name}_{facing.value}_walk"
            )
            anim_1 = (
                f"sprites/{self.npc.template.sprite_name}_{facing.value}.png"
            )
            images.append(f"{anim_0}.{str(0).zfill(3)}.png")
            images.append(anim_1)
            images.append(f"{anim_0}.{str(1).zfill(3)}.png")
            images.append(anim_1)

            frames: list[tuple[pygame.surface.Surface, float]] = []
            for image in images:
                surface = load_and_scale(image)
                frames.append((surface, frame_duration))

            _surfanim = surfanim.SurfaceAnimation(frames, loop=True)
            self.sprite[f"{facing.value}_walk"] = _surfanim

        self.surface_animations.add(self.sprite)

    def _calculate_frame_duration(self) -> float:
        """Calculate the frame duration for walking animations."""
        return (1000 / prepare.CONFIG.player_walkrate) / 3 / 1000 * 2

    def update(self, time_delta: float) -> None:
        """Update the sprite animation and position."""
        self.surface_animations.update(time_delta)
        self.rect.topleft = self.npc.tile_pos

    def get_frame(self, ani: str) -> pygame.surface.Surface:
        """Get the current frame of the sprite animation."""
        frame_dict: SpriteMap = (
            self.sprite if self.npc.moving else self.standing
        )
        if ani in frame_dict:
            frame = frame_dict[ani]
            if isinstance(frame, SurfaceAnimation):
                frame.rate = self.npc.moverate / prepare.CONFIG.player_walkrate
                return frame.get_current_frame()
            return frame
        raise ValueError(f"Animation '{ani}' not found.")
