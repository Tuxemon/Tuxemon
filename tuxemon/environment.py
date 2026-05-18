# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass

from pygame.rect import Rect
from pygame.surface import Surface

from tuxemon.database.runtime import db
from tuxemon.db import (
    BattleGraphicsModel,
    BattleHudModel,
    BattleMusicModel,
    EnvironmentModel,
)
from tuxemon.graphics import load_and_scale, load_raw_image, scale_surface
from tuxemon.prepare import DisplayContext

logger = logging.getLogger(__name__)


@dataclass
class PartyLayout:
    path: str
    init_pos: dict[str, int]
    target: dict[str, int]
    centerx: int
    offset: int

    @classmethod
    def create(
        cls,
        context: DisplayContext,
        side: str,
        home: Rect,
        hud: BattleHudModel,
        hud_layer: int,
    ) -> PartyLayout:
        center_off = context.scaling.scale_int(hud.tray_center_offset)
        spacing_off = context.scaling.scale_int(hud.icon_spacing_offset)

        if side == "opponent":
            return cls(
                path=hud.tray_opponent,
                init_pos={
                    "bottom": home.bottom,
                    "right": 0,
                    "layer": hud_layer,
                },
                target={"right": home.right},
                centerx=home.right - center_off,
                offset=spacing_off,
            )

        return cls(
            path=hud.tray_player,
            init_pos={
                "bottom": home.bottom,
                "left": home.right,
                "layer": hud_layer,
            },
            target={"left": home.left},
            centerx=home.left + center_off,
            offset=-spacing_off,
        )


@dataclass
class BattleLayout:
    back_island_pos: dict[str, int]
    front_island_pos: dict[str, int]
    offsets: dict[str, int]
    entry_jump_distance: int
    entry_duration: float

    @classmethod
    def create(
        cls,
        context: DisplayContext,
        graphics: BattleGraphicsModel,
        screen_rect: tuple[int, int],
        player_home: Rect,
        opp_home: Rect,
    ) -> BattleLayout:
        w, _ = screen_rect
        y_mod = context.scaling.scale_int(graphics.island_offset_y)

        return cls(
            back_island_pos={"bottom": opp_home.bottom + y_mod, "right": 0},
            front_island_pos={"bottom": player_home.bottom - y_mod, "left": w},
            offsets={
                "enemy_y": context.scaling.scale_int(
                    graphics.enemy_base_offset
                ),
                "monster_y": context.scaling.scale_int(
                    graphics.monster_base_offset
                ),
                "player_y": context.scaling.scale_int(
                    graphics.player_base_offset
                ),
            },
            entry_jump_distance=context.scaling.scale_int(
                graphics.entry_jump_distance
            ),
            entry_duration=graphics.entry_duration,
        )

    def get_combatant_pos(
        self, role: str, island_rect: Rect
    ) -> dict[str, int]:
        """Returns the bottom/centerx anchor for a sprite based on its role."""
        if role == "enemy":
            return {
                "bottom": island_rect.bottom - self.offsets["enemy_y"],
                "centerx": island_rect.centerx,
            }
        elif role == "monster":
            return {
                "bottom": island_rect.bottom - self.offsets["monster_y"],
                "centerx": island_rect.centerx,
            }
        elif role == "player":
            return {
                "bottom": island_rect.centery + self.offsets["player_y"],
                "centerx": island_rect.centerx,
            }
        return {}


class EnvironmentManager:
    """
    Central service for loading, unloading, and delegating access to
    environment-specific battle settings (graphics, music, etc.).
    Ensures safe access to the active environment context.
    """

    def __init__(self, context: DisplayContext) -> None:
        self.context = context
        self._active_handler: Environment | None = None
        self._override_lock: bool = False
        logger.debug("EnvironmentManager initialized.")

    def update(self, dt: float) -> None:
        if self._active_handler:
            self._active_handler.update(dt)

    def load_environment(self, slug: str) -> bool:
        """
        Loads a new environment by creating an EnvironmentData and Environment object.
        Returns True on success, False on failure.
        """
        if self._override_lock:
            logger.debug(f"Environment override active, ignoring load: {slug}")
            return False

        self._active_handler = None
        try:
            env_data = EnvironmentData(slug)
            self._active_handler = Environment(env_data, self.context)
            logger.debug(f"Successfully loaded environment: {slug}")
            return True
        except Exception as e:
            logger.error(f"Failed to load environment '{slug}': {e}")
            return False

    def unload_environment(self) -> None:
        """Explicitly unloads the current environment, often called when changing maps."""
        self._active_handler = None
        logger.debug("Environment unloaded.")

    def get_active_environment(self) -> Environment | None:
        """Returns the currently active Environment, or None if none is loaded."""
        return self._active_handler

    def lock_environment(self) -> None:
        self._override_lock = True

    def unlock_environment(self) -> None:
        self._override_lock = False

    def is_locked(self) -> bool:
        return self._override_lock


class EnvironmentData:
    """
    Loads environment configuration from the database using a slug.
    Provides access to graphics and music models. Acts as the data
    layer for Environment.
    """

    def __init__(self, slug: str) -> None:
        """
        Loads the environment data model based on the provided slug.
        """
        self.slug = slug
        try:
            self.environment_model = EnvironmentModel.lookup(slug, db)
        except RuntimeError as e:
            # EntryNotFoundError is wrapped into a RuntimeError in EnvironmentModel.lookup
            logger.error(str(e))
            raise e

    def get_battle_graphics(self) -> BattleGraphicsModel:
        """Returns the loaded battle graphics model."""
        return self.environment_model.battle_graphics

    def get_battle_music(self) -> BattleMusicModel:
        """Returns the loaded battle music model."""
        return self.environment_model.battle_music


class Environment:
    """
    Runtime wrapper around EnvironmentData. Exposes high-level accessors
    for graphics, music, and combat menu state used during battles.
    """

    def __init__(
        self, environment_data: EnvironmentData, context: DisplayContext
    ) -> None:
        self.data = environment_data
        self.context = context
        self.elapsed_time = 0.0
        self._party_layouts: dict[str, PartyLayout] = {}
        self._battle_layout: BattleLayout | None = None
        logger.debug(f"Environment initialized for slug: {self.data.slug}")

    def update(self, dt: float) -> None:
        self.elapsed_time += dt

    def get_battle_graphics(self) -> BattleGraphicsModel:
        return self.data.get_battle_graphics()

    def get_battle_music(self) -> BattleMusicModel:
        return self.data.get_battle_music()

    def get_battle_assets(self) -> dict[str, Surface]:
        graphics = self.data.get_battle_graphics()

        sheet = IslandSheet(
            context=self.context,
            file_path=graphics.island_sheet,
            frame_w=graphics.island_width,
            frame_h=graphics.island_height,
        )

        return {
            "island_back": sheet.back(),
            "island_front": sheet.front(),
        }

    def get_party_layout(
        self, side: str, home: Rect, hud_layer: int
    ) -> PartyLayout:
        if side not in self._party_layouts:
            hud = self.data.get_battle_graphics().hud
            self._party_layouts[side] = PartyLayout.create(
                self.context, side, home, hud, hud_layer
            )
        return self._party_layouts[side]

    def get_battle_layout(
        self, screen_rect: tuple[int, int], player_home: Rect, opp_home: Rect
    ) -> BattleLayout:
        if not self._battle_layout:
            graphics = self.data.get_battle_graphics()
            self._battle_layout = BattleLayout.create(
                self.context, graphics, screen_rect, player_home, opp_home
            )
        return self._battle_layout

    def prepare_background(self, screen_size: tuple[int, int]) -> Surface:
        """Processes the background sprite to fit the screen dimensions."""
        graphics = self.data.get_battle_graphics()
        scale_int = self.context.scale
        surf = load_and_scale(graphics.background, scale_int)

        full_width, full_height = screen_size
        full_surf = Surface((full_width, full_height))
        full_surf.fill((0, 0, 0))
        full_surf.blit(surf, (0, 0))

        # Stretch the last row to fill the bottom (for dialog area)
        if surf.get_height() < full_height:
            last_row = surf.subsurface(
                Rect(0, surf.get_height() - 1, surf.get_width(), 1)
            )
            for y in range(surf.get_height(), full_height):
                full_surf.blit(last_row, (0, y))

        return full_surf


class IslandSheet:
    def __init__(
        self,
        context: DisplayContext,
        file_path: str,
        frame_w: int,
        frame_h: int,
    ):
        self.context = context
        self.file_path = file_path
        self.frame_w = frame_w
        self.frame_h = frame_h
        self.frames = self._slice()

    def _slice(self) -> dict[str, Surface]:
        sheet = load_raw_image(self.file_path)
        w, h = sheet.get_size()

        expected_w = self.frame_w * 2
        expected_h = self.frame_h

        if (w, h) != (expected_w, expected_h):
            raise ValueError(
                f"Island sheet '{self.file_path}' must be "
                f"{expected_w}x{expected_h}, but is {w}x{h}"
            )

        back_raw = sheet.subsurface((0, 0, self.frame_w, self.frame_h))
        front_raw = sheet.subsurface(
            (self.frame_w, 0, self.frame_w, self.frame_h)
        )
        scale_int = self.context.scale
        back_scaled = scale_surface(back_raw, scale_int)
        front_scaled = scale_surface(front_raw, scale_int)

        return {
            "back": back_scaled,
            "front": front_scaled,
        }

    def back(self) -> Surface:
        return self.frames["back"]

    def front(self) -> Surface:
        return self.frames["front"]
