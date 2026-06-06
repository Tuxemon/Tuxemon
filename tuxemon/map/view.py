# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from itertools import chain
from typing import TYPE_CHECKING

from pygame import SRCALPHA
from pygame.draw import line
from pygame.gfxdraw import box
from pygame.rect import Rect
from pygame.surface import Surface

from tuxemon.animation_entity import AnimationManager
from tuxemon.camera.camera import project
from tuxemon.db import Direction, FacingMode
from tuxemon.graphics import (
    ColorLike,
    apply_cinema_bars,
    load_and_scale,
    slice_spritesheet_surface,
)
from tuxemon.map.map import get_pos_from_tilepos
from tuxemon.math import Vector2
from tuxemon.platform.const.graphics import BLACK_COLOR
from tuxemon.prepare import DISPLAY_CONTEXT, DisplayContext
from tuxemon.surfanim import SurfaceAnimation, SurfaceAnimationCollection
from tuxemon.user_config import CONFIG

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tuxemon.camera.camera import CameraManager
    from tuxemon.db import NpcTemplateModel
    from tuxemon.entity.appearance import RuntimeAppearance
    from tuxemon.entity.npc import NPC
    from tuxemon.map.manager import MapManager
    from tuxemon.map.tuxemon import AbstractMap
    from tuxemon.npc_manager import NPCManager


class EntityFacing(str, Enum):
    front = "front"
    back = "back"
    left = "left"
    right = "right"


DIRECTION_TO_FACING: dict[Direction, EntityFacing] = {
    Direction.UP: EntityFacing.back,
    Direction.DOWN: EntityFacing.front,
    Direction.LEFT: EntityFacing.left,
    Direction.RIGHT: EntityFacing.right,
}


@dataclass
class WorldSurfaces:
    surface: Surface
    position3: Vector2
    layer: int


sprite_cache: dict[str, Surface] = {}


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


class SpriteController:
    """
    Manages sprite rendering, updates, and animation states for an NPC.
    This controller never loads PNGs directly — all sprite logic lives
    in SpriteRenderer.
    """

    def __init__(self, npc: NPC) -> None:
        self.npc = npc
        self.sprite_renderer = SpriteRenderer(npc)
        self.sprite_renderer.load_sprites(npc.template)

    def update(self, dt: float) -> None:
        """
        Update the sprite renderer and reposition the sprite
        based on the NPC's current tile position.
        """
        self.sprite_renderer.set_position(self.npc.tile_pos)
        self.sprite_renderer.update(dt)

    def update_appearance(self, appearance: RuntimeAppearance) -> None:
        """
        Reload sprites using the NPC's template, but with runtime-overridden
        sprite/combat sheet names.
        """
        template = self.npc.template.model_copy()

        template.sprite_name = appearance.sprite_name
        template.combat_sheet = appearance.combat_sheet
        self.composited_sheet = (
            self.npc.appearance_manager.build_composited_sheet()
        )

        self.sprite_renderer.load_sprites(template)
        self.sprite_renderer.stop()
        self.sprite_renderer.surface_animations.clear()

        for anim in self.sprite_renderer.sprite.values():
            if isinstance(anim, SurfaceAnimation):
                self.sprite_renderer.surface_animations.add(anim)

        self.sprite_renderer.play()

    def get_animation_frame(self, ani: str) -> Surface:
        """Return the current animation frame for the given animation key."""
        return self.sprite_renderer.get_animation_frame(
            ani,
            self.sprite_renderer.sprite,
            self.npc,
        )

    def get_facing_frame(self, facing: EntityFacing) -> Surface:
        """Return the static standing frame for the given facing direction."""
        return self.sprite_renderer.get_facing_frame(
            facing,
            self.sprite_renderer.standing,
        )

    def play_animation(self, move_dir: Direction) -> None:
        """Play the sprite animation."""
        if self.npc.facing_mode != FacingMode.FOLLOW_MOVEMENT:
            facing = self.npc.facing.value
            ani_key = SpriteRenderer.ANIMATION_MAPPING["walking"][facing]
        else:
            ani_key = SpriteRenderer.ANIMATION_MAPPING["walking"][
                move_dir.value
            ]

        self.sprite_renderer.play(ani_key)

    def stop_animation(self) -> None:
        """Stop the sprite animation."""
        self.sprite_renderer.stop()

    def get_sprite_renderer(self) -> SpriteRenderer:
        """Return the underlying sprite renderer."""
        return self.sprite_renderer


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

    def __init__(self, npc: NPC) -> None:
        self.npc = npc
        self.standing: dict[EntityFacing, Surface] = {}
        self.sprite: dict[str, SurfaceAnimation] = {}
        self.surface_animations = SurfaceAnimationCollection()
        self.player_width = 0
        self.player_height = 0
        self.rect = Rect(0, 0, 0, 0)

        self.frame_duration = self._calculate_frame_duration(
            npc.template, npc.moverate
        )

    def load_sprites(self, template: NpcTemplateModel) -> None:
        """
        Load overworld sprites for this NPC.
        Uses a sprite sheet for animated NPCs and a single image for static props.
        """
        self.standing.clear()
        self.sprite.clear()
        self.surface_animations.clear()

        if template.is_static_prop:
            self._load_static_prop(template)
        else:
            self._load_from_sheet(template)

        self._set_sprite_position(self.npc.tile_pos)

    def _load_static_prop(self, template: NpcTemplateModel) -> None:
        """Load a single static sprite for props."""
        path = f"sprites_obj/{template.sprite_name}.png"
        surf = load_and_scale_with_cache(path)

        self.standing = {
            EntityFacing.front: surf,
            EntityFacing.back: surf,
            EntityFacing.left: surf,
            EntityFacing.right: surf,
        }
        self.sprite = {}

    def _load_from_sheet(self, template: NpcTemplateModel) -> None:
        """
        Load standing frames and walking animations from a sprite sheet.
        Sheet layout:
          rows: directions (front, left, right, back)
          columns: frames (walk1, idle, walk2)
        """
        sprite_controller = getattr(self.npc, "sprite_controller", None)

        if sprite_controller is not None and hasattr(
            sprite_controller, "composited_sheet"
        ):
            sheet = self.npc.sprite_controller.composited_sheet
        else:
            sheet_path = f"sprites/{template.sprite_name}.png"
            sheet = load_and_scale_with_cache(sheet_path)

        scaled_fw = template.frame_width * DISPLAY_CONTEXT.scale
        scaled_fh = template.frame_height * DISPLAY_CONTEXT.scale

        all_frames = slice_spritesheet_surface(
            sheet,
            scaled_fw,
            scaled_fh,
        )

        expected_frames = template.rows * template.columns
        if len(all_frames) != expected_frames:
            raise ValueError(
                f"Sprite sheet {len(all_frames)} frames, "
                f"but expected {expected_frames} ({template.rows}x{template.columns})"
            )

        row_map = {
            EntityFacing.front: 0,
            EntityFacing.left: 1,
            EntityFacing.right: 2,
            EntityFacing.back: 3,
        }

        for facing, row_index in row_map.items():
            start = row_index * template.columns
            end = start + template.columns
            frames = all_frames[start:end]

            idle_frame = frames[1]
            self.standing[facing] = idle_frame

            idle_anim = SurfaceAnimation([(idle_frame, 999999)])
            self.sprite[f"{facing.value}"] = idle_anim

            anim_frames = [
                (frames[1], self.frame_duration),
                (frames[0], self.frame_duration),
                (frames[1], self.frame_duration),
                (frames[2], self.frame_duration),
            ]
            walk_anim = SurfaceAnimation(anim_frames)
            self.sprite[f"{facing.value}_walk"] = walk_anim
            self.surface_animations.add(walk_anim)

    def _set_sprite_position(self, tile_pos: tuple[int, int]) -> None:
        """Sets the sprite's position with an offset for tall sprites."""
        self.player_width, self.player_height = self.standing[
            EntityFacing.front
        ].get_size()

        y_offset = max(0, self.player_height - DISPLAY_CONTEXT.tile_size[1])

        self.rect = Rect(
            tile_pos[0],
            tile_pos[1] - y_offset,
            self.player_width,
            self.player_height,
        )

    def set_position(self, position: tuple[int, int]) -> None:
        """Set the position of the sprite."""
        self.rect.topleft = position

    def _calculate_frame_duration(
        self,
        template: NpcTemplateModel,
        rate: float = CONFIG.player_walkrate,
        time_scale: int = 1000,
    ) -> float:
        """Calculate frame duration using NPC-specific animation parameters."""
        return (
            (time_scale / rate)
            / template.frame_divisor
            / time_scale
            * template.speed_factor
            * template.animation_speed
        )

    def update(self, dt: float) -> None:
        """Update all registered animations."""
        self.surface_animations.update(dt)

    def get_animation_frame(
        self, ani: str, animations: dict[str, SurfaceAnimation], npc: NPC
    ) -> Surface:
        """Get current frame from animation dictionary."""
        if ani not in animations:
            raise ValueError(f"Animation '{ani}' not found.")
        animation = animations[ani]
        animation.rate = npc.moverate / CONFIG.player_walkrate
        return animation.get_current_frame()

    def get_facing_frame(
        self, facing: EntityFacing, sprites: dict[EntityFacing, Surface]
    ) -> Surface:
        """Get static frame based on facing direction."""
        if facing not in sprites:
            raise ValueError(f"Facing '{facing}' not found.")
        return sprites[facing]

    def play(self, ani_key: str | None = None) -> None:
        """Play the sprite animation.

        If ani_key is provided, switch to that animation first.
        Otherwise, just resume whatever is currently active.
        """
        if ani_key is not None:
            animation = self.sprite[ani_key]
            self.surface_animations.clear()
            self.surface_animations.add(animation)

        self.surface_animations.play()

    def stop(self) -> None:
        """Stop all sprite animations."""
        self.surface_animations.stop()


class AbstractRenderer(ABC):
    """Interface for all map rendering implementations."""

    layer_color: ColorLike | None
    bubble_manager: BubbleManager
    cinema_x_ratio: float | None
    cinema_y_ratio: float | None
    map_animations: AnimationManager

    @property
    @abstractmethod
    def label(self) -> str:
        """A string identifier for the renderer."""
        ...

    @abstractmethod
    def update(self, dt: float) -> None:
        """Update internal state, animations, etc."""

    @abstractmethod
    def draw(self, surface: Surface, current_map: AbstractMap | None) -> None:
        """Draw the map and related elements to the surface."""


class NullRenderer(AbstractRenderer):
    """A no-op renderer for when no map is loaded."""

    def __init__(self) -> None:
        pass

    @property
    def label(self) -> str:
        return "null_renderer"

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: Surface, current_map: AbstractMap | None) -> None:
        surface.fill(BLACK_COLOR)


class MapRenderer(AbstractRenderer):
    """Renders the game map, NPCs, and animations."""

    def __init__(
        self,
        camera_manager: CameraManager,
        npc_manager: NPCManager,
        debug_renderer: DebugRenderer,
        context: DisplayContext,
    ):
        """Initializes the MapRenderer."""
        self.camera_manager = camera_manager
        self.npc_manager = npc_manager
        self.debug_renderer = debug_renderer
        self.context = context
        self.layer = Surface(context.rect.size, SRCALPHA)
        self.layer_color: ColorLike | None = None
        self.cinema_x_ratio: float | None = None
        self.cinema_y_ratio: float | None = None
        self.map_animations = AnimationManager()
        self.bubble_manager = BubbleManager(context=context)
        self.layer_image: bool = False

    @property
    def label(self) -> str:
        return "map_renderer"

    def draw(self, surface: Surface, current_map: AbstractMap | None) -> None:
        """Draws the map, sprites, and animations onto the given surface."""
        if current_map is None:
            raise ValueError(
                "MapRenderer requires a valid AbstractMap to draw."
            )
        self._prepare_map_rendering(current_map)
        screen_surfaces = self._get_and_position_surfaces(current_map)
        self._draw_map_and_sprites(surface, screen_surfaces, current_map)
        if self.layer_color or self.layer_image:
            self._apply_effects(surface)
        self._apply_cinema_bars(surface)
        if CONFIG.collision_map:
            self.debug_renderer.draw_debug(current_map, surface)

    def update(self, dt: float) -> None:
        """Update the map animations."""
        self.camera_manager.update(dt)
        self.map_animations.update_all(dt)

    def _prepare_map_rendering(self, current_map: AbstractMap) -> None:
        """Prepares the map renderer for drawing."""
        if current_map.renderer is None:
            current_map.initialize_renderer()
        if current_map.renderer is None:
            raise RuntimeError("Map renderer could not be initialized.")
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
            apply_bars(
                self.context, "horizontal", self.cinema_x_ratio, surface
            )
        if self.cinema_y_ratio is not None:
            apply_bars(self.context, "vertical", self.cinema_y_ratio, surface)

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
                info.animation.get_current_frame(),
                Vector2(info.position),
                info.layer,
            )
            for info in self.map_animations._cache.values()
            if info.visible and not info.animation.is_finished()
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
            screen_position = get_pos_from_tilepos(
                current_map, self.context, position
            )
            rect = Rect(screen_position, surface.get_size())
            if surface.get_height() > self.context.tile_size[1]:
                rect.y -= surface.get_height() // 2
            screen_surfaces.append((surface, rect, layer))
        return screen_surfaces

    def _get_sprites(self, npc: NPC, layer: int) -> list[WorldSurfaces]:
        """Retrieves sprite surfaces for an NPC."""
        sprite_renderer = npc.sprite_controller.get_sprite_renderer()

        if npc.mover.is_moving_state:
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

        pixel_x, pixel_y = npc.position
        return [WorldSurfaces(frame, Vector2(pixel_x, pixel_y), layer)]


class BubbleManager:
    """Manages the creation, updating, and rendering of speech bubbles."""

    def __init__(
        self,
        context: DisplayContext,
        layer: int = 100,
        offset_divisor: int = 10,
    ):
        self._bubbles: dict[NPC, Surface] = {}
        self.context = context
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
                current_map, self.context, entity_pos_vector
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
        context: DisplayContext,
        event_color: ColorLike = (0, 255, 0, 128),
        collision_color: ColorLike = (255, 0, 0, 128),
        center_line_color: ColorLike = (255, 50, 50),
    ) -> None:
        self.map_manager = map_manager
        self.npc_manager = npc_manager
        self.context = context
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
            vector = Vector2(event.box.x, event.box.y)
            topleft = get_pos_from_tilepos(current_map, self.context, vector)
            size = project(self.context, (event.box.width, event.box.height))
            rect = topleft, size
            box(surface, rect, self.event_color)

    def _draw_collision_tiles(
        self, current_map: AbstractMap, surface: Surface
    ) -> None:
        # We need to iterate over all collidable objects. Start with walls/collision boxes.
        box_iter = map(
            lambda box: collision_box_to_pgrect(
                current_map, self.context, box
            ),
            self.map_manager.collision_map,
        )

        # Next, deal with solid NPCs.
        npc_iter = map(
            lambda npc: npc_to_pgrect(current_map, self.context, npc),
            self.npc_manager.npcs.values(),
        )
        for item in chain(box_iter, npc_iter):
            box(surface, item, self.collision_color)

    def _draw_center_lines(self, surface: Surface) -> None:
        w, h = surface.get_size()
        cx, cy = w // 2, h // 2
        line(surface, self.center_line_color, (cx, 0), (cx, h))
        line(surface, self.center_line_color, (0, cy), (w, cy))


def apply_bars(
    context: DisplayContext,
    orientation: str,
    aspect_ratio: float,
    screen: Surface,
) -> None:
    apply_cinema_bars(
        aspect_ratio,
        screen,
        orientation,
        context.rect.size,
        BLACK_COLOR,
    )


def collision_box_to_pgrect(
    current_map: AbstractMap, context: DisplayContext, box: tuple[int, int]
) -> Rect:
    """
    Returns a Rect (in screen-coords) version of a collision box (in world-coords).
    """
    x, y = get_pos_from_tilepos(current_map, context, Vector2(box))
    tw, th = context.tile_size
    return Rect(x, y, tw, th)


def npc_to_pgrect(
    current_map: AbstractMap, context: DisplayContext, npc: NPC
) -> Rect:
    """Returns a Rect (in screen-coords) version of an NPC's bounding box."""
    pos = get_pos_from_tilepos(current_map, context, npc.position)
    return Rect(pos, context.tile_size)
    return Rect(pos, context.tile_size)
