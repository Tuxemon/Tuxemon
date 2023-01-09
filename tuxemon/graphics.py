# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""

General "tools" code for pygame graphics operations that don't
have a home in any specific place.

"""
from __future__ import annotations

import logging
import os
import re
from typing import (
    TYPE_CHECKING,
    Any,
    Generator,
    Iterable,
    Optional,
    Protocol,
    Sequence,
    Tuple,
    Union,
)

import pygame
from pytmx.pytmx import TileFlags
from pytmx.util_pygame import handle_transformation, smart_convert

from tuxemon import prepare
from tuxemon.session import Session
from tuxemon.sprite import Sprite
from tuxemon.surfanim import SurfaceAnimation
from tuxemon.tools import scale_sequence, transform_resource_filename

if TYPE_CHECKING:
    from tuxemon.client import LocalPygameClient

logger = logging.getLogger(__name__)


ColorLike = Union[
    pygame.color.Color,
    str,
    Tuple[int, int, int],
    Tuple[int, int, int, int],
]


class LoaderProtocol(Protocol):
    def __call__(
        self,
        rect: Optional[Tuple[int, int, int, int]] = None,
        flags: Optional[TileFlags] = None,
    ) -> pygame.surface.Surface:
        pass


def strip_from_sheet(
    sheet: pygame.surface.Surface,
    start: Tuple[int, int],
    size: Tuple[int, int],
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
    coords: Sequence[Tuple[int, int]],
    size: Tuple[int, int],
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


def load_and_scale(filename: str) -> pygame.surface.Surface:
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
    return scale_surface(load_image(filename), prepare.SCALE)


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
    directory: str,
    name: str,
) -> Generator[pygame.surface.Surface, None, None]:
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

    For example, water00.png, water01.png, water02.png.

    Parameters:
        directory: Directory where the frames are located.
        name: Name of the animation (common prefix of the frames).

    Returns:
        Sequence of filenames.

    """
    frames = list()
    pattern = re.compile(rf"{name}\.?_?[0-9]+\.png")
    # might be slow on large folders
    for filename in os.listdir(directory):
        if pattern.match(filename):
            frames.append(os.path.join(directory, filename))
    frames.sort()
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


def load_animation_from_frames(
    directory: str,
    name: str,
    duration: float,
    loop: bool = False,
) -> SurfaceAnimation:
    """
    Load animation from a collection of frame files.

    Parameters:
        directory: Directory where the frames are located.
        name: Name of the animation (common prefix of the frames).
        duration: Duration in seconds.
        loop: Whether the animation should loop or not.

    Returns:
        Created animation.

    """
    frames = load_frames_files(directory, name)
    return create_animation(frames, duration, loop)


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
    sprite._original_image = pygame.transform.scale(
        sprite._original_image,
        sprite.rect.size,
    )
    sprite._needs_update = True


def convert_alpha_to_colorkey(
    surface: pygame.surface.Surface,
    colorkey: ColorLike = (255, 0, 255),
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
        rect: Optional[Tuple[int, int, int, int]] = None,
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


def get_avatar(
    session: Session,
    avatar: str,
) -> Optional[Sprite]:
    """
    Gets the avatar sprite of a monster or NPC.

    Used to parse the string values for dialog event actions.
    If avatar is a number, we're referring to a monster slot in
    the player's party.
    If avatar is a string, we're referring to a monster by name.
    TODO: If the monster name isn't found, we're referring to an NPC
    on the map.

    Parameters:
        session: Game session.
        avatar: The identifier of the avatar to be used.

    Returns:
        The surface of the monster or NPC avatar sprite.

    """
    # TODO: remove the need for this import
    from tuxemon.monster import Monster

    if avatar and avatar.isdigit():
        try:
            player = session.player
            slot = int(avatar)
            return player.monsters[slot].get_sprite("menu")
        except IndexError:
            logger.debug("invalid avatar monster slot")
            return None
    else:
        try:
            # TODO: don't create a new monster just to load the sprite
            avatar_monster = Monster()
            avatar_monster.load_from_db(avatar)
            avatar_monster.flairs = {}  # Don't use random flair graphics
            return avatar_monster.get_sprite("menu")
        except KeyError:
            logger.debug("invalid avatar monster name")
            return None
