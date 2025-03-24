# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""

General "tools" code for pygame graphics operations that don't
have a home in any specific place.

"""
from __future__ import annotations

import logging
import os
import re
from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING, Any, Optional, Protocol, Union

import pygame
from pytmx.pytmx import TileFlags
from pytmx.util_pygame import handle_transformation, smart_convert

from tuxemon import prepare
from tuxemon.db import db
from tuxemon.session import Session
from tuxemon.sprite import Sprite
from tuxemon.surfanim import SurfaceAnimation
from tuxemon.tools import scale_sequence, transform_resource_filename

if TYPE_CHECKING:
    from tuxemon.client import LocalPygameClient

logger = logging.getLogger(__name__)


ColorLike = Union[
    pygame.color.Color,
    tuple[int, int, int],
    tuple[int, int, int, int],
]


class LoaderProtocol(Protocol):
    def __call__(
        self,
        rect: Optional[tuple[int, int, int, int]] = None,
        flags: Optional[TileFlags] = None,
    ) -> pygame.surface.Surface:
        pass


def strip_from_sheet(
    sheet: pygame.surface.Surface,
    start: tuple[int, int],
    size: tuple[int, int],
    columns: int,
    rows: int = 1,
) -> Sequence[pygame.surface.Surface]:
    """
    Strips individual frames from a sprite sheet.

    Parameters:
        sheet: Sprite sheet.
        start: Start location in the sheet.
        size: Size of the sprite.
        columns: Number of columns.
        rows: Number of rows.

    Returns:
        Sequence of stripped frames.

    """
    frames = []
    for j in range(rows):
        for i in range(columns):
            location = (start[0] + size[0] * i, start[1] + size[1] * j)
            frames.append(sheet.subsurface(pygame.rect.Rect(location, size)))
    return frames


def strip_coords_from_sheet(
    sheet: pygame.surface.Surface,
    coords: Sequence[tuple[int, int]],
    size: tuple[int, int],
) -> Sequence[pygame.surface.Surface]:
    """
    Strip specific coordinates from a sprite sheet.

    Parameters:
        sheet: Sprite sheet.
        coords: Locations in the sheet.
        size: Size of the sprite.

    Returns:
        Sequence of stripped frames.

    """
    frames = []
    for coord in coords:
        location = (coord[0] * size[0], coord[1] * size[1])
        frames.append(sheet.subsurface(pygame.rect.Rect(location, size)))
    return frames


def cursor_from_image(image: pygame.surface.Surface) -> Sequence[str]:
    """Take a valid image and create a mouse cursor."""
    colors = {(0, 0, 0, 255): "X", (255, 255, 255, 255): "."}
    rect = image.get_rect()
    icon_string = []
    for j in range(rect.height):
        this_row = []
        for i in range(rect.width):
            pixel = tuple(image.get_at((i, j)))
            this_row.append(colors.get(pixel, " "))
        icon_string.append("".join(this_row))
    return icon_string


def load_and_scale(
    filename: str, scale: float = prepare.SCALE
) -> pygame.surface.Surface:
    """
    Load an image and scale it according to game settings.

    * Filename will be transformed to be loaded from game resource folder
    * Will be converted if needed
    * Scale factor will match game setting

    Parameters:
        filename: Path of the image file.

    Returns:
        Loaded and scaled image.

    """
    return scale_surface(load_image(filename), scale)


def load_image(filename: str) -> pygame.surface.Surface:
    """Load image from the resources folder

    * Filename will be transformed to be loaded from game resource folder
    * Will be converted if needed.

    This is a "smart" loader, and will convert files in the best way,
    but is slightly slower than just loading.  Its important that
    this is not called too often (like once per draw!)

    Parameters:
        filename: Path of the image file.

    Returns:
        Loaded image.

    """
    filename = transform_resource_filename(filename)
    return smart_convert(pygame.image.load(filename), None, True)


def load_sprite(
    filename: str,
    **rect_kwargs: Any,
) -> Sprite:
    """
    Load an image from disk and return a sprite.

    Image name will be transformed and converted.
    Rect attribute will be set.

    Any keyword arguments will be passed to the get_rect method
    of the image for positioning the rect.

    Parameters:
        filename: Filename to load.
        rect_kwargs: Parameters for ``get_rect``.

    Returns:
        Loaded sprite.

    """
    sprite = Sprite(image=load_and_scale(filename))
    sprite.rect = sprite.image.get_rect(**rect_kwargs)
    return sprite


def load_animated_sprite(
    filenames: Iterable[str],
    delay: float,
) -> Sprite:
    """
    Load a set of images and return an animated sprite.

    Image name will be transformed and converted.
    Rect attribute will be set.

    Any keyword arguments will be passed to the get_rect method
    of the image for positioning the rect.

    Parameters:
        filenames: Filenames to load.
        delay: Frame interval; time between each frame.

    Returns:
        Loaded animated sprite.

    """
    anim = []
    for filename in filenames:
        if os.path.exists(filename):
            image = load_and_scale(filename)
            anim.append((image, delay))

    tech = SurfaceAnimation(anim, True)
    tech.play()
    return Sprite(animation=tech)


def scale_surface(
    surface: pygame.surface.Surface,
    factor: float,
) -> pygame.surface.Surface:
    """Scale a surface. Just a shortcut."""
    return pygame.transform.scale(
        surface,
        [int(i * factor) for i in surface.get_size()],
    )


def load_frames_files(
    directory: str, name: str
) -> Iterable[pygame.surface.Surface]:
    """
    Load frames from filenames.

    For example, water00.png, water01.png, water03.png.

    Parameters:
        directory: Directory where the frames are located.
        name: Name of the animation (common prefix of the frames).

    Yields:
        Loaded and scaled frames.

    """
    for filename in animation_frame_files(directory, name):
        yield load_and_scale(filename)


def animation_frame_files(
    directory: str,
    name: str,
) -> Sequence[str]:
    r"""
    Return list of filenames from directory for use in animation.

    * each filename will have the format: animation_name[0-9]*\..*
    * will be returned in sorted order

    For example, water_00.png, water_01.png, water_02.png.

    Parameters:
        directory: Directory where the frames are located.
        name: Name of the animation (common prefix of the frames).

    Returns:
        Sequence of filenames.

    """
    pattern = re.compile(rf"{name}\.?_?[0-9]+\.png")
    frames = [
        os.path.join(directory, filename)
        for filename in sorted(os.listdir(directory))
        if pattern.match(filename)
    ]
    return frames


def create_animation(
    frames: Iterable[pygame.surface.Surface],
    duration: float,
    loop: bool,
) -> SurfaceAnimation:
    """
    Create animation from frames, a list of surfaces.

    Parameters:
        frames: Surfaces used to create the animation.
        duration: Duration in seconds.
        loop: Whether the animation should loop or not.

    Returns:
        Created animation.

    """
    data = [(f, duration) for f in frames]
    animation = SurfaceAnimation(data, loop=loop)
    return animation


def scale_tile(
    surface: pygame.surface.Surface,
    tile_size: int,
) -> pygame.surface.Surface:
    """
    Scales a map tile based on resolution.

    Parameters:
        surface: Surface to rescale.
        tile_size: Desired size.

    Returns:
        The rescaled surface.

    """
    if type(surface) is pygame.Surface:
        surface = pygame.transform.scale(surface, tile_size)
    else:
        surface.scale(tile_size)

    return surface


def scale_sprite(
    sprite: Sprite,
    ratio: float,
) -> None:
    """
    Scale a sprite's image in place.

    Parameters:
        sprite: Sprite to rescale.
        ratio: Amount to scale by.

    """
    center = sprite.rect.center
    sprite.rect.width = int(sprite.rect.width * ratio)
    sprite.rect.height = int(sprite.rect.height * ratio)
    sprite.rect.center = center
    assert sprite._original_image
    sprite._original_image = pygame.transform.scale(
        sprite._original_image,
        sprite.rect.size,
    )
    sprite._needs_update = True


def convert_alpha_to_colorkey(
    surface: pygame.surface.Surface,
    colorkey: ColorLike = prepare.FUCHSIA_COLOR,
) -> pygame.surface.Surface:
    """
    Convert image with per-pixel alpha to normal surface with colorkey.

    This is a crude hack that only works well with images that do not
    have alpha blended antialiased edges.  Using this function on such
    images will result in discoloration of edges.

    Parameters:
        surface: Image with per-pixel alpha.
        colorkey: Colorkey to use for transparency.

    Returns:
        New surface with colorkey.

    """
    image = pygame.Surface(surface.get_size())
    image.fill(colorkey)
    image.set_colorkey(colorkey)
    image.blit(surface, (0, 0))
    return image


def scaled_image_loader(
    filename: str,
    colorkey: Optional[str],
    *,
    pixelalpha: bool = True,
    **kwargs: Any,
) -> LoaderProtocol:
    """
    Pytmx image loader for pygame.

    Modified to load images at a scaled size.

    Parameters:
        filename: Path of the image.
        colorkey: Hex values of the transparency color.
        pixelalpha: Whether to use per-pixel alpha transparency or not.
        kwargs: Ignored parameters passed in the loader.

    Returns:
        The loader to use.

    """
    colorkey_color = pygame.Color(f"#{colorkey}") if colorkey else None

    # load the tileset image
    image = pygame.image.load(filename)

    # scale the tileset image to match game scale
    scaled_size = scale_sequence(image.get_size())
    image = pygame.transform.scale(image, scaled_size)

    def load_image(
        rect: Optional[tuple[int, int, int, int]] = None,
        flags: Optional[TileFlags] = None,
    ) -> pygame.surface.Surface:
        if rect:
            # scale the rect to match the scaled image
            rect = scale_sequence(rect)
            try:
                tile = image.subsurface(rect)
            except ValueError:
                logger.error("Tile bounds outside bounds of tileset image")
                raise
        else:
            tile = image.copy()

        if flags:
            tile = handle_transformation(tile, flags)

        tile = smart_convert(tile, colorkey_color, pixelalpha)
        return tile

    return load_image


def capture_screenshot(game: LocalPygameClient) -> pygame.surface.Surface:
    """
    Capture a screenshot of the current map.

    Parameters:
        game: The game object.

    Returns:
        The captured screenshot.

    """
    from tuxemon.states.world.worldstate import WorldState

    screenshot = pygame.Surface(game.screen.get_size())
    world = game.get_state_by_name(WorldState)
    world.draw(screenshot)
    return screenshot


def get_avatar(session: Session, avatar: Union[str, int]) -> Optional[Sprite]:
    """
    Retrieves the avatar sprite of a monster or NPC.

    Parameters:
        session: Game session.
        avatar: The identifier of the avatar to be used.

    Returns:
        The surface of the monster or NPC avatar sprite, or None if not found.

    """
    if isinstance(avatar, int):
        try:
            return session.player.monsters[avatar].get_sprite("menu")
        except IndexError:
            logger.debug(f"Invalid avatar monster slot: {avatar}")
            return None

    if avatar in db.database["monster"]:
        monster = db.lookup(avatar, table="monster")
        if not monster.sprites:
            logger.warning(f"Monster '{avatar}' has no sprites")
            return None
        menu_sprites = [
            transform_resource_filename(f"{monster.sprites.menu1}.png"),
            transform_resource_filename(f"{monster.sprites.menu2}.png"),
        ]
        return load_animated_sprite(menu_sprites, 0.25)

    if avatar in db.database["npc"]:
        npc = db.lookup(avatar, table="npc")
        path = f"gfx/sprites/player/{npc.template.combat_front}.png"
        sprite = load_sprite(path)
        scale_sprite(sprite, 0.5)
        return sprite

    logger.debug(f"Avatar '{avatar}' not found")
    return None


def string_to_colorlike(
    color: str,
) -> ColorLike:
    """
    It converts a string into a ColorLike.

    Parameters:
        color: string (eg: 255:255:255).

    Returns:
        The ColorLike.

    """
    rgb: ColorLike = prepare.BLACK_COLOR
    part = color.split(":")
    rgb = (
        (int(part[0]), int(part[1]), int(part[2]), int(part[3]))
        if len(part) == 4
        else (int(part[0]), int(part[1]), int(part[2]))
    )
    return rgb
