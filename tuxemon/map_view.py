# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, Union

import pygame

from tuxemon import prepare, surfanim
from tuxemon.db import EntityFacing
from tuxemon.graphics import ColorLike, load_and_scale
from tuxemon.map import proj
from tuxemon.math import Vector2
from tuxemon.surfanim import SurfaceAnimation

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tuxemon.camera import Camera
    from tuxemon.map import TuxemonMap
    from tuxemon.npc import NPC
    from tuxemon.states.world.worldstate import WorldState

SpriteMap = Union[
    dict[str, SurfaceAnimation], dict[str, pygame.surface.Surface]
]


@dataclass
class AnimationInfo:
    animation: SurfaceAnimation
    position: tuple[int, int]
    layer: int


@dataclass
class WorldSurfaces:
    surface: pygame.surface.Surface
    position3: Vector2
    layer: int


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


class MapRenderer:
    """Renders the game map, NPCs, and animations."""

    def __init__(
        self, world_state: WorldState, screen: pygame.Surface, camera: Camera
    ):
        """Initializes the MapRenderer."""
        self.world_state = world_state
        self.screen = screen
        self.camera = camera
        self.layer = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        self.layer_color: ColorLike = prepare.TRANSPARENT_COLOR
        self.bubble: dict[NPC, pygame.surface.Surface] = {}
        self.cinema_x_ratio: Optional[float] = None
        self.cinema_y_ratio: Optional[float] = None
        self.map_animations: dict[str, AnimationInfo] = {}

    def draw(
        self, surface: pygame.surface.Surface, current_map: TuxemonMap
    ) -> None:
        """Draws the map, sprites, and animations onto the given surface."""
        self._prepare_map_rendering(current_map)
        screen_surfaces = self._get_and_position_surfaces(
            current_map.sprite_layer
        )
        self._draw_map_and_sprites(surface, screen_surfaces, current_map)
        self._apply_effects(surface)
        self._apply_cinema_bars(surface)
        if prepare.CONFIG.collision_map:
            self.debug_drawing(surface)

    def update(self, time_delta: float) -> None:
        """Update the map animations."""
        for anim_data in self.map_animations.values():
            anim_data.animation.update(time_delta)

    def _prepare_map_rendering(self, current_map: TuxemonMap) -> None:
        """Prepares the map renderer for drawing."""
        if current_map.renderer is None:
            current_map.initialize_renderer()
        camera_x, camera_y = self.camera.position
        assert current_map.renderer
        current_map.renderer.center((camera_x, camera_y))

    def _get_and_position_surfaces(
        self, sprite_layer: int
    ) -> list[tuple[pygame.surface.Surface, pygame.rect.Rect, int]]:
        """Retrieves and positions surfaces for rendering."""
        npc_surfaces = self._get_npc_surfaces(sprite_layer)
        map_animations = self._get_map_animations()
        surfaces = npc_surfaces + map_animations
        screen_surfaces = self._position_surfaces(surfaces)
        self._set_bubble(screen_surfaces)
        return screen_surfaces

    def _draw_map_and_sprites(
        self,
        surface: pygame.surface.Surface,
        screen_surfaces: list[
            tuple[pygame.surface.Surface, pygame.rect.Rect, int]
        ],
        current_map: TuxemonMap,
    ) -> None:
        """Draws the map and sprites onto the surface."""
        assert current_map.renderer
        current_map.renderer.draw(surface, surface.get_rect(), screen_surfaces)

    def _apply_effects(self, surface: pygame.surface.Surface) -> None:
        """Applies visual effects to the surface."""
        self._set_layer(surface)

    def _apply_cinema_bars(self, surface: pygame.surface.Surface) -> None:
        """Applies cinema bars (letterboxing) to the surface."""
        if self.cinema_x_ratio is not None:
            self._apply_horizontal_bars(self.cinema_x_ratio, surface)
        if self.cinema_y_ratio is not None:
            self._apply_vertical_bars(self.cinema_y_ratio, surface)

    def _get_npc_surfaces(self, current_map: int) -> list[WorldSurfaces]:
        """Retrieves surfaces for NPCs."""
        return [
            surf
            for npc in self.world_state.npcs
            for surf in self._get_sprites(npc, current_map)
        ]

    def _get_map_animations(self) -> list[WorldSurfaces]:
        """Retrieves surfaces for map animations."""
        return [
            WorldSurfaces(
                anim.get_current_frame(), Vector2(data.position), data.layer
            )
            for data in self.map_animations.values()
            for anim in [data.animation]
            if not anim.is_finished() and anim.visibility
        ]

    def _position_surfaces(
        self, surfaces: list[WorldSurfaces]
    ) -> list[tuple[pygame.surface.Surface, pygame.rect.Rect, int]]:
        """Positions surfaces on the screen."""
        screen_surfaces = []
        for frame in surfaces:
            surface = frame.surface
            position = frame.position3
            layer = frame.layer
            screen_position = self.world_state.get_pos_from_tilepos(position)
            rect = pygame.rect.Rect(screen_position, surface.get_size())
            if surface.get_height() > prepare.TILE_SIZE[1]:
                rect.y -= surface.get_height() // 2
            screen_surfaces.append((surface, rect, layer))
        return screen_surfaces

    def _set_bubble(
        self,
        screen_surfaces: list[
            tuple[pygame.surface.Surface, pygame.rect.Rect, int]
        ],
    ) -> None:
        """Adds speech bubbles to the screen surfaces."""
        if self.bubble:
            for npc, surface in self.bubble.items():
                center_x, center_y = self.world_state.get_pos_from_tilepos(
                    Vector2(npc.tile_pos)
                )
                bubble_rect = surface.get_rect()
                bubble_rect.centerx = npc.sprite_renderer.rect.centerx
                bubble_rect.bottom = npc.sprite_renderer.rect.top
                bubble_rect.x = center_x
                bubble_rect.y = center_y - (
                    surface.get_height()
                    + int(npc.sprite_renderer.rect.height / 10)
                )
                screen_surfaces.append((surface, bubble_rect, 100))

    def _set_layer(self, surface: pygame.surface.Surface) -> None:
        """Applies the layer effect to the surface."""
        self.layer.fill(self.layer_color)
        surface.blit(self.layer, (0, 0))

    def _get_sprites(self, npc: NPC, layer: int) -> list[WorldSurfaces]:
        """Retrieves sprite surfaces for an NPC."""
        sprite_renderer = npc.sprite_renderer
        moving = "walking" if npc.moving else "idle"
        state = sprite_renderer.ANIMATION_MAPPING[moving][npc.facing.value]
        frame = sprite_renderer.get_frame(state)
        return [WorldSurfaces(frame, proj(npc.position3), layer)]

    def debug_drawing(self, surface: pygame.surface.Surface) -> None:
        """Draws debug information on the surface."""
        self.world_state.debug_drawing(surface)

    def _apply_vertical_bars(
        self,
        aspect_ratio: float,
        screen: pygame.surface.Surface,
    ) -> None:
        """Applies vertical cinema bars."""
        screen_aspect_ratio = prepare.SCREEN_SIZE[0] / prepare.SCREEN_SIZE[1]
        if screen_aspect_ratio < aspect_ratio:
            bar_height = int(
                prepare.SCREEN_SIZE[1]
                * (1 - screen_aspect_ratio / aspect_ratio)
                / 2
            )
            bar = pygame.Surface((prepare.SCREEN_SIZE[0], bar_height))
            bar.fill(prepare.BLACK_COLOR)
            screen.blit(bar, (0, 0))
            screen.blit(bar, (0, prepare.SCREEN_SIZE[1] - bar_height))

    def _apply_horizontal_bars(
        self,
        aspect_ratio: float,
        screen: pygame.surface.Surface,
    ) -> None:
        """Applies horizontal cinema bars."""
        screen_aspect_ratio = prepare.SCREEN_SIZE[1] / prepare.SCREEN_SIZE[0]
        if screen_aspect_ratio < aspect_ratio:
            bar_width = int(
                prepare.SCREEN_SIZE[0]
                * (1 - screen_aspect_ratio / aspect_ratio)
                / 2
            )
            bar = pygame.Surface((bar_width, prepare.SCREEN_SIZE[1]))
            bar.fill(prepare.BLACK_COLOR)
            screen.blit(bar, (0, 0))
            screen.blit(bar, (prepare.SCREEN_SIZE[0] - bar_width, 0))
