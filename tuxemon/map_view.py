# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, Union

import pygame

from tuxemon import prepare
from tuxemon.db import EntityFacing
from tuxemon.graphics import ColorLike, load_and_scale
from tuxemon.map import proj
from tuxemon.math import Vector2
from tuxemon.surfanim import SurfaceAnimation, SurfaceAnimationCollection

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tuxemon.camera import Camera
    from tuxemon.db import NpcTemplateModel
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


sprite_cache: dict[str, pygame.surface.Surface] = {}
standing_sprite_cache: dict[
    str, dict[EntityFacing, pygame.surface.Surface]
] = {}
walking_sprite_cache: dict[str, SurfaceAnimation] = {}


def load_and_scale_with_cache(file_path: str) -> pygame.surface.Surface:
    """
    Load and scale an image, using a cache to avoid redundant file operations.
    """
    if file_path not in sprite_cache:
        try:
            sprite_cache[file_path] = load_and_scale(file_path)
        except Exception as e:
            logger.error(f"Failed to load sprite: {file_path} - {e}")
            raise
    return sprite_cache[file_path]


def load_walking_animations_with_cache(
    template: NpcTemplateModel, facing: EntityFacing, frame_duration: float
) -> SurfaceAnimation:
    """
    Load walking animations with caching to avoid redundant frame processing.
    """
    cache_key = f"{template.sprite_name}_{facing.value}_walk"
    if cache_key not in walking_sprite_cache:
        logger.info(f"Creating new walking animation for: {cache_key}")
        images: list[str] = [
            f"sprites/{template.sprite_name}_{facing.value}_walk.{str(0).zfill(3)}.png",
            f"sprites/{template.sprite_name}_{facing.value}.png",
            f"sprites/{template.sprite_name}_{facing.value}_walk.{str(1).zfill(3)}.png",
            f"sprites/{template.sprite_name}_{facing.value}.png",
        ]
        frames: list[tuple[pygame.surface.Surface, float]] = [
            (load_and_scale_with_cache(image), frame_duration)
            for image in images
        ]
        walking_sprite_cache[cache_key] = SurfaceAnimation(frames, loop=True)
    else:
        logger.info(f"Using cached walking animation for: {cache_key}")
    return walking_sprite_cache[cache_key]


def clear_standing_cache(cache_key: str) -> None:
    """Clears a specific item from the standing cache."""
    if cache_key in standing_sprite_cache:
        del standing_sprite_cache[cache_key]
        logger.info(f"Cleared cache for: {cache_key}")
    else:
        logger.info(f"No cache found for: {cache_key}")


def clear_walking_cache(cache_key: str) -> None:
    """Clears a specific item from the walking cache."""
    if cache_key in walking_sprite_cache:
        del walking_sprite_cache[cache_key]
        logger.info(f"Cleared cache for: {cache_key}")
    else:
        logger.info(f"No cache found for: {cache_key}")


class SpriteController:
    """Manages the sprite rendering, updates, and animation states for an NPC."""

    def __init__(self, npc: NPC) -> None:
        self.npc = npc
        self.sprite_renderer = SpriteRenderer()
        self.sprite_renderer.load_sprites(self.npc.template, self.npc.tile_pos)

    def update(self, time_delta: float) -> None:
        """Update the sprite renderer."""
        self.sprite_renderer.set_position(self.npc.tile_pos)
        self.sprite_renderer.update(time_delta)

    def update_template(self, template: NpcTemplateModel) -> None:
        """Update the NPC template and reload sprites."""
        self.sprite_renderer.load_sprites(template, self.npc.tile_pos)
        self.sprite_renderer.stop()
        self.sprite_renderer.surface_animations.clear()
        self.sprite_renderer.surface_animations.add(
            self.sprite_renderer.sprite
        )
        self.sprite_renderer.play()

    def get_frame(self, ani: str) -> pygame.surface.Surface:
        """Get the current frame of the sprite animation."""
        return self.sprite_renderer.get_frame(ani, self.npc)

    def get_sprite_renderer(self) -> SpriteRenderer:
        """Returns the sprite renderer."""
        return self.sprite_renderer

    def load_sprites(self, template: NpcTemplateModel) -> None:
        """Load sprite graphics based on the template."""
        self.sprite_renderer.load_sprites(template, self.npc.tile_pos)

    def play_animation(self) -> None:
        """Play the sprite animation."""
        self.sprite_renderer.play()

    def stop_animation(self) -> None:
        """Stop the sprite animation."""
        self.sprite_renderer.stop()


class SpriteRenderer:
    """Handles loading, updating, and rendering of sprite animations."""

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

    def __init__(self) -> None:
        """Initialize the SpriteRenderer."""
        self.standing: dict[
            Union[EntityFacing, str], pygame.surface.Surface
        ] = {}
        self.sprite: dict[str, SurfaceAnimation] = {}
        self.surface_animations = SurfaceAnimationCollection()
        self.player_width = 0
        self.player_height = 0
        self.rect = pygame.rect.Rect(0, 0, 0, 0)
        self.frame_duration = self._calculate_frame_duration()

    def load_sprites(
        self, template: NpcTemplateModel, tile_pos: tuple[int, int]
    ) -> None:
        self._load_standing_sprites(template)
        self._load_walking_sprites(template)
        self._set_sprite_position(tile_pos)

    def _load_standing_sprites(self, template: NpcTemplateModel) -> None:
        """Loads the static standing sprites for different facings of an NPC."""
        if template.sprite_name not in standing_sprite_cache:
            is_interactive_object = template.slug == "interactive_obj"
            sprite_dict = {}
            for facing in EntityFacing:
                filename = (
                    f"{template.sprite_name}.png"
                    if is_interactive_object
                    else f"{template.sprite_name}_{facing.value}.png"
                )
                path = os.path.join(
                    "sprites_obj" if is_interactive_object else "sprites",
                    filename,
                )
                sprite_dict[facing] = load_and_scale_with_cache(path)
            standing_sprite_cache[template.sprite_name] = sprite_dict
        else:
            logger.info(
                f"Using cached standing sprites: {template.sprite_name}"
            )

        self.standing = standing_sprite_cache[template.sprite_name]

    def _load_walking_sprites(self, template: NpcTemplateModel) -> None:
        """Loads walking animations for the NPC based on the given template."""
        if template.slug != "interactive_obj":
            self._load_walking_animations(template)

    def _set_sprite_position(self, tile_pos: tuple[int, int]) -> None:
        """Sets the sprite's position and dimensions based on tile coordinates."""
        self.player_width, self.player_height = self.standing[
            EntityFacing.front
        ].get_size()
        self.rect = pygame.rect.Rect(
            (
                tile_pos[0],
                tile_pos[1],
                self.player_width,
                self.player_height,
            )
        )

    def _load_walking_animations(self, template: NpcTemplateModel) -> None:
        """Loads and initializes the walking animation frames for the NPC."""
        for facing in EntityFacing:
            animation = load_walking_animations_with_cache(
                template, facing, self.frame_duration
            )
            self.sprite[f"{facing.value}_walk"] = animation
        self.surface_animations.add(self.sprite)

    def _calculate_frame_duration(self) -> float:
        """Calculate the frame duration for walking animations."""
        return (1000 / prepare.CONFIG.player_walkrate) / 3 / 1000 * 2

    def set_position(self, position: tuple[int, int]) -> None:
        """Set the position of the sprite."""
        self.rect.topleft = position

    def update(self, time_delta: float) -> None:
        """Update the sprite animation."""
        self.surface_animations.update(time_delta)

    def get_frame(self, ani: str, npc: NPC) -> pygame.surface.Surface:
        """Get the current frame of the sprite animation."""
        frame_dict: SpriteMap = self.sprite if npc.moving else self.standing
        if ani in frame_dict:
            frame = frame_dict[ani]
            if isinstance(frame, SurfaceAnimation):
                frame.rate = npc.moverate / prepare.CONFIG.player_walkrate
                return frame.get_current_frame()
            return frame
        raise ValueError(f"Animation '{ani}' not found.")

    def play(self) -> None:
        """Play the sprite animation."""
        self.surface_animations.play()

    def stop(self) -> None:
        """Stop the sprite animation."""
        self.surface_animations.stop()


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
                sprite_renderer = npc.sprite_controller.get_sprite_renderer()
                center_x, center_y = self.world_state.get_pos_from_tilepos(
                    Vector2(npc.tile_pos)
                )
                bubble_rect = surface.get_rect()
                bubble_rect.centerx = sprite_renderer.rect.centerx
                bubble_rect.bottom = sprite_renderer.rect.top
                bubble_rect.x = center_x
                bubble_rect.y = center_y - (
                    surface.get_height()
                    + int(sprite_renderer.rect.height / 10)
                )
                screen_surfaces.append((surface, bubble_rect, 100))

    def _set_layer(self, surface: pygame.surface.Surface) -> None:
        """Applies the layer effect to the surface."""
        self.layer.fill(self.layer_color)
        surface.blit(self.layer, (0, 0))

    def _get_sprites(self, npc: NPC, layer: int) -> list[WorldSurfaces]:
        """Retrieves sprite surfaces for an NPC."""
        sprite_renderer = npc.sprite_controller.get_sprite_renderer()
        moving = "walking" if npc.moving else "idle"
        state = sprite_renderer.ANIMATION_MAPPING[moving][npc.facing.value]
        frame = sprite_renderer.get_frame(state, npc)
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
