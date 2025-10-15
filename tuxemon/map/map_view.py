# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from itertools import chain
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import pygame
from pygame.draw import line
from pygame.gfxdraw import box
from pygame.rect import Rect
from pygame.surface import Surface

from tuxemon import prepare
from tuxemon.camera.camera import project
from tuxemon.db import Direction
from tuxemon.entity import EntityState
from tuxemon.graphics import ColorLike, apply_cinema_bars, load_and_scale
from tuxemon.map.map import get_pos_from_tilepos, proj
from tuxemon.math import Vector2
from tuxemon.surfanim import SurfaceAnimation, SurfaceAnimationCollection

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tuxemon.camera.camera import CameraManager
    from tuxemon.db import NpcTemplateModel
    from tuxemon.map.map_manager import MapManager
    from tuxemon.map.map_tuxemon import AbstractMap
    from tuxemon.npc import NPC
    from tuxemon.npc_manager import NPCManager


class EntityFacing(str, Enum):
    front = "front"
    back = "back"
    left = "left"
    right = "right"


DIRECTION_TO_FACING: dict[Direction, EntityFacing] = {
    Direction.up: EntityFacing.back,
    Direction.down: EntityFacing.front,
    Direction.left: EntityFacing.left,
    Direction.right: EntityFacing.right,
}


@dataclass
class AnimationInfo:
    animation: SurfaceAnimation
    position: tuple[int, int]
    layer: int


@dataclass
class WorldSurfaces:
    surface: Surface
    position3: Vector2
    layer: int


sprite_cache: dict[str, Surface] = {}
standing_sprite_cache: dict[str, dict[EntityFacing, Surface]] = {}


def load_and_scale_with_cache(file_path: str) -> Surface:
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
    Load walking animations without caching.
    """
    logger.info(
        f"Loading new walking animation for: {template.sprite_name}, {facing.value}"
    )
    images: list[str] = [
        f"sprites/{template.sprite_name}_{facing.value}_walk.{str(0).zfill(3)}.png",
        f"sprites/{template.sprite_name}_{facing.value}.png",
        f"sprites/{template.sprite_name}_{facing.value}_walk.{str(1).zfill(3)}.png",
        f"sprites/{template.sprite_name}_{facing.value}.png",
    ]
    frames: list[tuple[Surface, float]] = [
        (load_and_scale_with_cache(image), frame_duration) for image in images
    ]
    return SurfaceAnimation(frames, loop=True)


def clear_standing_cache(cache_key: str) -> None:
    """Clears a specific item from the standing cache."""
    if cache_key in standing_sprite_cache:
        del standing_sprite_cache[cache_key]
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
        self.sprite_renderer.set_position(
            self.npc.tile_pos, self.npc.body.position.z
        )
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

    def get_animation_frame(self, ani: str) -> Surface:
        """Returns the current animation frame for the given animation key."""
        return self.sprite_renderer.get_animation_frame(
            ani, self.sprite_renderer.sprite, self.npc
        )

    def get_facing_frame(self, facing: EntityFacing) -> Surface:
        """Returns the static sprite frame for the given facing direction."""
        return self.sprite_renderer.get_facing_frame(
            facing, self.sprite_renderer.standing
        )

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
        "running": {
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
        "jumping": {
            "up": "back_walk",
            "down": "front_walk",
            "left": "left_walk",
            "right": "right_walk",
        },
    }

    def __init__(self) -> None:
        """Initialize the SpriteRenderer."""
        self.standing: dict[EntityFacing, Surface] = {}
        self.sprite: dict[str, SurfaceAnimation] = {}
        self.surface_animations = SurfaceAnimationCollection()
        self.player_width = 0
        self.player_height = 0
        self.rect = Rect(0, 0, 0, 0)
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
                path = (
                    Path("sprites_obj" if is_interactive_object else "sprites")
                    / filename
                )
                sprite_dict[facing] = load_and_scale_with_cache(
                    path.as_posix()
                )
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
        self.rect = Rect(
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

    def _calculate_frame_duration(
        self,
        rate: float = prepare.CONFIG.player_walkrate,
        time_scale: int = 1000,
        frame_divisor: int = 3,
        speed_factor: float = 2,
    ) -> float:
        """Calculate the frame duration for walking animations."""
        return (time_scale / rate) / frame_divisor / time_scale * speed_factor

    def set_position(
        self, position: tuple[int, int], z_offset: float = 0.0
    ) -> None:
        """Set the position of the sprite, optionally offset by vertical jump."""
        self.rect.topleft = (position[0], position[1] - int(z_offset))

    def update(self, time_delta: float) -> None:
        """Update the sprite animation."""
        self.surface_animations.update(time_delta)

    def get_animation_frame(
        self, ani: str, animations: dict[str, SurfaceAnimation], npc: NPC
    ) -> Surface:
        """Get current frame from animation dictionary."""
        if ani not in animations:
            raise ValueError(f"Animation '{ani}' not found.")
        animation = animations[ani]
        animation.rate = npc.moverate / prepare.CONFIG.player_walkrate
        return animation.get_current_frame()

    def get_facing_frame(
        self, facing: EntityFacing, sprites: dict[EntityFacing, Surface]
    ) -> Surface:
        """Get static frame based on facing direction."""
        if facing not in sprites:
            raise ValueError(f"Facing '{facing}' not found.")
        return sprites[facing]

    def play(self) -> None:
        """Play the sprite animation."""
        self.surface_animations.play()

    def stop(self) -> None:
        """Stop the sprite animation."""
        self.surface_animations.stop()


class MapRenderer:
    """Renders the game map, NPCs, and animations."""

    def __init__(
        self,
        camera_manager: CameraManager,
        npc_manager: NPCManager,
        debug_renderer: DebugRenderer,
    ):
        """Initializes the MapRenderer."""
        self.camera_manager = camera_manager
        self.npc_manager = npc_manager
        self.debug_renderer = debug_renderer
        self.layer = Surface(prepare.SCREEN_SIZE, pygame.SRCALPHA)
        self.layer_color: Optional[ColorLike] = None
        self.cinema_x_ratio: Optional[float] = None
        self.cinema_y_ratio: Optional[float] = None
        self.map_animations: dict[str, AnimationInfo] = {}
        self.bubble_manager = BubbleManager()

    def draw(self, surface: Surface, current_map: AbstractMap) -> None:
        """Draws the map, sprites, and animations onto the given surface."""
        self._prepare_map_rendering(current_map)
        screen_surfaces = self._get_and_position_surfaces(current_map)
        self._draw_map_and_sprites(surface, screen_surfaces, current_map)
        if self.layer_color:
            self._apply_effects(surface)
        self._apply_cinema_bars(surface)
        if prepare.CONFIG.collision_map:
            self.debug_renderer.draw_debug(current_map, surface)

    def update(self, time_delta: float) -> None:
        """Update the map animations."""
        self.camera_manager.update(time_delta)
        for anim_data in self.map_animations.values():
            anim_data.animation.update(time_delta)

    def _prepare_map_rendering(self, current_map: AbstractMap) -> None:
        """Prepares the map renderer for drawing."""
        if current_map.renderer is None:
            current_map.initialize_renderer()
        camera = self.camera_manager.get_active_camera()
        center = camera.get_viewport_center() if camera else Vector2(0, 0)
        assert current_map.renderer
        current_map.renderer.center(center)

    def _get_and_position_surfaces(
        self, current_map: AbstractMap
    ) -> list[tuple[Surface, Rect, int]]:
        """Retrieves and positions surfaces for rendering."""
        npc_surfaces = self._get_npc_surfaces(current_map.sprite_layer)
        map_animations = self._get_map_animations()
        surfaces = npc_surfaces + map_animations
        screen_surfaces = self._position_surfaces(current_map, surfaces)
        screen_surfaces.extend(
            self.bubble_manager.get_rendered_bubbles(current_map)
        )
        return screen_surfaces

    def _draw_map_and_sprites(
        self,
        surface: Surface,
        screen_surfaces: list[tuple[Surface, Rect, int]],
        current_map: AbstractMap,
    ) -> None:
        """Draws the map and sprites onto the surface."""
        assert current_map.renderer
        current_map.renderer.draw(surface, surface.get_rect(), screen_surfaces)

    def _apply_effects(self, surface: Surface) -> None:
        """Applies visual effects to the surface."""
        if self.layer_color and self.layer.get_at((0, 0)) != self.layer_color:
            self.layer.fill(self.layer_color)
        surface.blit(self.layer, (0, 0))

    def _apply_cinema_bars(self, surface: Surface) -> None:
        """Applies cinema bars (letterboxing) to the surface."""
        if self.cinema_x_ratio is not None:
            apply_bars("horizontal", self.cinema_x_ratio, surface)
        if self.cinema_y_ratio is not None:
            apply_bars("vertical", self.cinema_y_ratio, surface)

    def _get_npc_surfaces(self, sprite_layer: int) -> list[WorldSurfaces]:
        """Retrieves surfaces for NPCs."""
        return [
            surf
            for npc in self.npc_manager.npcs.values()
            for surf in self._get_sprites(npc, sprite_layer)
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
        self, current_map: AbstractMap, surfaces: list[WorldSurfaces]
    ) -> list[tuple[Surface, Rect, int]]:
        """Positions surfaces on the screen."""
        screen_surfaces = []
        for frame in surfaces:
            surface = frame.surface
            position = frame.position3
            layer = frame.layer
            screen_position = get_pos_from_tilepos(current_map, position)
            rect = Rect(screen_position, surface.get_size())
            if surface.get_height() > prepare.TILE_SIZE[1]:
                rect.y -= surface.get_height() // 2
            screen_surfaces.append((surface, rect, layer))
        return screen_surfaces

    def _get_sprites(self, npc: NPC, layer: int) -> list[WorldSurfaces]:
        """Retrieves sprite surfaces for an NPC."""
        sprite_renderer = npc.sprite_controller.get_sprite_renderer()

        if npc.mover.state in (
            EntityState.WALKING,
            EntityState.RUNNING,
            EntityState.JUMPING,
        ):
            ani_key = sprite_renderer.ANIMATION_MAPPING[npc.mover.state.value][
                npc.facing.value
            ]
            frame = sprite_renderer.get_animation_frame(
                ani_key, sprite_renderer.sprite, npc
            )
        else:
            frame = sprite_renderer.get_facing_frame(
                DIRECTION_TO_FACING[npc.facing],
                sprite_renderer.standing,
            )

        pixel_x, pixel_y = proj(npc.position)
        z_offset = npc.body.position.z if npc.is_airborne else 0.0
        adjusted_y = pixel_y - z_offset
        return [WorldSurfaces(frame, Vector2(pixel_x, adjusted_y), layer)]


class BubbleManager:
    """Manages the creation, updating, and rendering of speech bubbles."""

    def __init__(self, layer: int = 100, offset_divisor: int = 10):
        self._bubbles: dict[NPC, Surface] = {}
        self.layer = layer
        self.offset_divisor = offset_divisor

    def add_bubble(self, entity: NPC, surface: Surface) -> None:
        self._bubbles[entity] = surface

    def remove_bubble(self, entity: NPC) -> None:
        if self.has_bubble(entity):
            del self._bubbles[entity]

    def has_bubble(self, entity: NPC) -> bool:
        return entity in self._bubbles

    def clear_all_bubbles(self) -> None:
        self._bubbles.clear()

    def get_rendered_bubbles(
        self, current_map: AbstractMap
    ) -> list[tuple[Surface, Rect, int]]:
        """
        Calculates and returns a list of surfaces, their screen positions,
        and layers for all active bubbles.
        """
        rendered_bubbles: list[tuple[Surface, Rect, int]] = []
        if not self._bubbles:
            return rendered_bubbles

        for entity, surface in self._bubbles.items():
            sprite_renderer = entity.sprite_controller.get_sprite_renderer()
            entity_pos_vector = Vector2(entity.tile_pos)
            center_x, center_y = get_pos_from_tilepos(
                current_map, entity_pos_vector
            )
            bubble_rect = surface.get_rect()

            # Position bubble relative to the entity's sprite rect
            bubble_rect.centerx = center_x + (sprite_renderer.rect.width // 2)
            bubble_rect.bottom = center_y - int(
                sprite_renderer.rect.height / self.offset_divisor
            )
            rendered_bubbles.append((surface, bubble_rect, self.layer))
        return rendered_bubbles


class DebugRenderer:
    def __init__(
        self,
        map_manager: MapManager,
        npc_manager: NPCManager,
        event_color: ColorLike = (0, 255, 0, 128),
        collision_color: ColorLike = (255, 0, 0, 128),
        center_line_color: ColorLike = (255, 50, 50),
    ) -> None:
        self.map_manager = map_manager
        self.npc_manager = npc_manager
        self.event_color = event_color
        self.collision_color = collision_color
        self.center_line_color = center_line_color

    def draw_debug(self, current_map: AbstractMap, surface: Surface) -> None:
        """Draws debug information on the surface."""
        surface.lock()
        self._draw_events(current_map, surface)
        self._draw_collision_tiles(current_map, surface)
        self._draw_center_lines(surface)
        surface.unlock()

    def _draw_events(self, current_map: AbstractMap, surface: Surface) -> None:
        """Draws event-related debug information on the surface."""
        for event in self.map_manager.events:
            vector = Vector2(event.x, event.y)
            topleft = get_pos_from_tilepos(current_map, vector)
            size = project((event.w, event.h))
            rect = topleft, size
            box(surface, rect, self.event_color)

    def _draw_collision_tiles(
        self, current_map: AbstractMap, surface: Surface
    ) -> None:
        # We need to iterate over all collidable objects. Start with walls/collision boxes.
        box_iter = map(
            lambda box: collision_box_to_pgrect(current_map, box),
            self.map_manager.collision_map,
        )

        # Next, deal with solid NPCs.
        npc_iter = map(
            lambda npc: npc_to_pgrect(current_map, npc),
            self.npc_manager.npcs.values(),
        )
        for item in chain(box_iter, npc_iter):
            box(surface, item, self.collision_color)

    def _draw_center_lines(self, surface: Surface) -> None:
        w, h = surface.get_size()
        cx, cy = w // 2, h // 2
        line(surface, self.center_line_color, (cx, 0), (cx, h))
        line(surface, self.center_line_color, (0, cy), (w, cy))


def apply_bars(orientation: str, aspect_ratio: float, screen: Surface) -> None:
    apply_cinema_bars(
        aspect_ratio,
        screen,
        orientation,
        prepare.SCREEN_SIZE,
        prepare.BLACK_COLOR,
    )


def collision_box_to_pgrect(
    current_map: AbstractMap, box: tuple[int, int]
) -> Rect:
    """
    Returns a Rect (in screen-coords) version of a collision box (in world-coords).
    """
    x, y = get_pos_from_tilepos(current_map, Vector2(box))
    tw, th = prepare.TILE_SIZE
    return Rect(x, y, tw, th)


def npc_to_pgrect(current_map: AbstractMap, npc: NPC) -> Rect:
    """Returns a Rect (in screen-coords) version of an NPC's bounding box."""
    pos = get_pos_from_tilepos(current_map, proj(npc.position))
    return Rect(pos, prepare.TILE_SIZE)
