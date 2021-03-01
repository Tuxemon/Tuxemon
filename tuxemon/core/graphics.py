"""

General "tools" code for pygame graphics operations that don't
have a home in any specific place

"""

import logging
import os
import re

import pygame
from pytmx.util_pygame import smart_convert, handle_transformation

from tuxemon.compat import Rect
from tuxemon.core import prepare
from tuxemon.core.pyganim import PygAnimation, PygConductor
from tuxemon.core.sprite import Sprite
from tuxemon.core.tools import transform_resource_filename, scale_sequence, scale_rect

logger = logging.getLogger(__name__)


def strip_from_sheet(sheet, start, size, columns, rows=1):
    """Strips individual frames from a sprite sheet given a start location,
    sprite size, and number of columns and rows."""
    frames = []
    for j in range(rows):
        for i in range(columns):
            location = (start[0] + size[0] * i, start[1] + size[1] * j)
            frames.append(sheet.subsurface(Rect(location, size)))
    return frames


def strip_coords_from_sheet(sheet, coords, size):
    """Strip specific coordinates from a sprite sheet."""
    frames = []
    for coord in coords:
        location = (coord[0] * size[0], coord[1] * size[1])
        frames.append(sheet.subsurface(Rect(location, size)))
    return frames


def cursor_from_image(image):
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


def load_and_scale(filename):
    """ Load an image and scale it according to game settings

    * Filename will be transformed to be loaded from game resource folder
    * Will be converted if needed.
    * Scale factor will match game setting.

    :param filename:
    :rtype: pygame.Surface
    """
    return scale_surface(load_image(filename), prepare.SCALE)


def load_image(filename):
    """ Load image from the resources folder

    * Filename will be transformed to be loaded from game resource folder
    * Will be converted if needed.

    This is a "smart" loader, and will convert files in the best way,
    but is slightly slower than just loading.  Its important that
    this is not called too often (like once per draw!)

    :param filename: String
    :rtype: pygame.Surface
    """
    filename = transform_resource_filename(filename)
    return smart_convert(pygame.image.load(filename), None, True)


def load_sprite(filename, **rect_kwargs):
    """ Load an image from disk and return a pygame sprite

    Image name will be transformed and converted
    Rect attribute will be set

    Any keyword arguments will be passed to the get_rect method
    of the image for positioning the rect.

    :param filename: Filename to load
    :rtype: tuxemon.core.sprite.Sprite
    """
    sprite = Sprite()
    sprite.image = load_and_scale(filename)
    sprite.rect = sprite.image.get_rect(**rect_kwargs)
    return sprite


def load_animated_sprite(filenames, delay, **rect_kwargs):
    """ Load a set of images and return an animated pygame sprite

    Image name will be transformed and converted
    Rect attribute will be set

    Any keyword arguments will be passed to the get_rect method
    of the image for positioning the rect.

    :param filenames: Filenames to load
    :param int delay: Frame interval; time between each frame
    :rtype: tuxemon.core.sprite.Sprite
    """
    anim = []
    for filename in filenames:
        if os.path.exists(filename):
            image = load_and_scale(filename)
            anim.append((image, delay))

    tech = PygAnimation(anim, True)
    tech.play()
    sprite = Sprite()
    sprite.image = tech
    sprite.rect = sprite.image.get_rect(**rect_kwargs)
    return sprite


def scale_surface(surface, factor):
    """ Scale a surface.  Just a shortcut.

    :returns: Scaled surface
    :rtype: pygame.Surface
    """
    return pygame.transform.scale(
        surface, [int(i * factor) for i in surface.get_size()]
    )


def load_frames_files(directory, name):
    """ Load frames from filenames

    For example, water00.png, water01.png, water03.png

    :type directory: str
    :type name: str
    :rtype: Iterator[pygame.surface.Surface]
    """
    for filename in animation_frame_files(directory, name):
        yield load_and_scale(filename)


def animation_frame_files(directory, name):
    r""" Return list of filenames from directory for use in animation

    * each filename will have the format: animation_name[0-9]*\..*
    * will be returned in sorted order

    For example, water00.png, water01.png, water02.png

    :param str directory:
    :param str name:
    :rtype: List[str]
    """
    frames = list()
    pattern = r"{}[0-9]*\..*".format(name)
    # might be slow on large folders
    for filename in os.listdir(directory):
        if re.match(pattern, filename):
            frames.append(os.path.join(directory, filename))
    frames.sort()
    return frames


def create_animation(frames, duration, loop):
    """ Create animation from frames, a list of surfaces

    :param frames:
    :param duration:
    :param loop:
    :return:
    """
    data = [(f, duration) for f in frames]
    animation = PygAnimation(data, loop=loop)
    conductor = PygConductor({"animation": animation})
    return animation, conductor


def load_animation_from_frames(directory, name, duration, loop=False):
    """ Load animation from a collection of frame files

    :param directory:
    :param name:
    :param duration:
    :param loop:

    :return:
    """
    frames = load_frames_files(directory, name)
    return create_animation(frames, duration, loop)


def scale_tile(surface, tile_size):
    """ Scales a map tile based on resolution.

    :type surface: pygame.Surface
    :type tile_size: int
    :rtype: pygame.Surface
    """
    if type(surface) is pygame.Surface:
        surface = pygame.transform.scale(surface, tile_size)
    else:
        surface.scale(tile_size)

    return surface


def scale_sprite(sprite, ratio):
    """ Scale a sprite's image in place

    :type sprite: pygame.Sprite
    :param ratio: amount to scale by
    :rtype: tuxemon.core.sprite.Sprite
    """
    center = sprite.rect.center
    sprite.rect.width *= ratio
    sprite.rect.height *= ratio
    sprite.rect.center = center
    sprite._original_image = pygame.transform.scale(
        sprite._original_image, sprite.rect.size
    )
    sprite._needs_update = True


def convert_alpha_to_colorkey(surface, colorkey=(255, 0, 255)):
    """ Convert image with perpixel alpha to normal surface with colorkey

    This is a crude hack that only works well with images that do not
    have alpha blended antialiased edges.  Using this function on such
    images will result in discoloration of edges.

    :param surface: Some image to change
    :type surface: pygame.Surface
    :param colorkey: Colorkey to use for transparency
    :type colorkey: Sequence or pygame.Color

    :returns: Modified surface
    :rtype: pygame.Surface
    """
    image = pygame.Surface(surface.get_size())
    image.fill(colorkey)
    image.set_colorkey(colorkey)
    image.blit(surface, (0, 0))
    return image


def scaled_image_loader(filename, colorkey, **kwargs):
    """ pytmx image loader for pygame

    Modified to load images at a scaled size

    :param filename:
    :param colorkey:
    :param kwargs:
    :return:
    """
    if colorkey:
        colorkey = pygame.Color("#{}".format(colorkey))

    pixelalpha = kwargs.get("pixelalpha", True)

    # load the tileset image
    image = pygame.image.load(filename)

    # scale the tileset image to match game scale
    scaled_size = scale_sequence(image.get_size())
    image = pygame.transform.scale(image, scaled_size)

    def load_image(rect=None, flags=None):
        if rect:
            # scale the rect to match the scaled image
            rect = scale_rect(rect)
            try:
                tile = image.subsurface(rect)
            except ValueError:
                logger.error("Tile bounds outside bounds of tileset image")
                raise
        else:
            tile = image.copy()

        if flags:
            tile = handle_transformation(tile, flags)

        tile = smart_convert(tile, colorkey, pixelalpha)
        return tile

    return load_image


def capture_screenshot(game):
    screenshot = pygame.Surface(game.screen.get_size())
    world = game.get_state_by_name("WorldState")
    world.draw(screenshot)
    return screenshot


def get_avatar(session, avatar):
    """Gets the avatar sprite of a monster or NPC.

    Used to parse the string values for dialog event actions
    If avatar is a number, we're referring to a monster slot in the player's party
    If avatar is a string, we're referring to a monster by name
    TODO: If the monster name isn't found, we're referring to an NPC on the map

    :param tuxemon.core.session.Session session:
    :param avatar: the avatar to be used
    :type avatar: string
    :rtype: Optional[pygame.Surface]
    :returns: The surface of the monster or NPC avatar sprite
    """
    # TODO: remove the need for this import
    from tuxemon.core.monster import Monster

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
