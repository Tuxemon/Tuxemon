# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
#
# fusion Module to fuse the face and body of two sprites.
#               Based on Pokemon Fusion by Alex Onsager
#               http://www.alexonsager.net/blog/2013/06/04/behind-the-scenes-pokemon-fusion/
#


# Note: this script, in its current state, is non-functional and the Tuxemon selected here
# serve only as examples of potential fusions.
from __future__ import annotations

import json
import logging
from collections.abc import Mapping
from typing import Any, Optional

from PIL import Image as PILImage
from PIL.Image import Image

logger = logging.getLogger(__name__)


class Body:
    """
    A class that holds data for use with fusing two sprites together.

    Example:
        Two Tuxemon can be fused by joining the face of one with the
        body of another.

        >>> sapsnap = Body()
        >>> # Load the sprite data from a json file
        >>> sapsnap.load('fusion/Sapsnap.json')
        >>>
        >>> vivitron = Body()
        >>> # Load the sprite data from a json file
        >>> vivitron.load('fusion/Vivitron.json')
        >>>
        >>> # Fuse the sprites.
        >>> fuse(body=sapsnap, face=vivitron)
        >>> fuse(body=vivitron, face=sapsnap)

    """

    face_image: Image
    body_image: Image

    def __init__(self) -> None:
        # Name properties
        self.prefix = ""  # A name prefix to use when fusing sprites
        self.suffix = ""  # A name suffix to use when fusing sprites

        # The full name of the sprite when you concat prefix + suffix
        self.name = ""

        # Face Properties
        self.face_image_path = ""  # The path to the face image to use.

        # The face size can be automatically obtained through
        # self.get_face_size()
        self.face_size = (0, 0)

        # The head size differs from the face size to take beaks,
        # etc. into account.
        self.head_size = (0, 0)
        # The center of the face.
        self.face_center = (0, 0)

        # Body properties
        # The path to the body image to use.
        self.body_image_path = ""
        # The center of the face on the body.
        self.face_position = (0, 0)

        # Colors
        self.primary_colors = [
            (0, 0, 0),
            (0, 0, 0),
            (0, 0, 0),
            (0, 0, 0),
            (0, 0, 0),
        ]  # 5 primary colors of the sprite
        self.secondary_colors = [
            (0, 0, 0),
            (0, 0, 0),
            (0, 0, 0),
            (0, 0, 0),
            (0, 0, 0),
        ]  # 5 secondary colors of the sprite
        self.tertiary_colors = [
            (0, 0, 0),
            (0, 0, 0),
            (0, 0, 0),
            (0, 0, 0),
            (0, 0, 0),
        ]  # 5 tertiary colors of the sprite

    def get_face_size(self) -> tuple[int, int]:
        """
        Obtains the size of the face image in pixels.

        It also sets the instance's face_size to the returned value.

        Returns:
            A tuple (x, y) of the face size in pixels.

        """

        img = self.face_image
        img = img.convert("RGBA")
        self.face_size = img.getdata().size

        return self.face_size

    def to_json(self) -> str:
        """
        Converts the current instance to a dictionary and converts it to json.

        Returns:
            A json string of the current instance.

        """

        body_dict = self.__dict__
        del body_dict["body_image"]
        del body_dict["face_image"]

        return json.dumps(body_dict)

    def save(self, filename: Optional[str] = None) -> None:
        """
        Saves the current instance and all its properties to a json file.

        Parameters:
            filename: The path to the file to save.

        """

        if not filename:
            filename = "fusion/%s.json" % self.name

        output = self.to_json()
        with open(filename, "w") as f:
            f.write(output)

    def load(self, json_data: str, file: bool = True) -> None:
        """
        Loads and sets all the properties to the properties in a json.

        Parameters:
            json_data: The string of json text or the file path to a json file
                to load.
            file: True or false value of whether or not "json_data" is a file
                path.

        Example:

            >>> sapsnap = Body()
            >>> sapsnap.load('fusion/Sapsnap.json')

        """
        # If "file" is set to true, then assume that json_data is a path to a
        # file containing json.
        if file:
            with open(json_data) as f:
                json_data = "".join(f.readlines())

        # Load the json data and convert it to a dictionary.
        body_dict = json.loads(json_data)

        # Set the name from the json data
        self.prefix = body_dict["prefix"]
        self.suffix = body_dict["suffix"]
        self.name = body_dict["name"]

        # Set the face properties from the json data
        self.face_image_path = body_dict["face_image_path"]
        self.face_size = tuple(body_dict["face_size"])
        self.head_size = tuple(body_dict["head_size"])
        self.face_center = tuple(body_dict["face_center"])

        # Set the body properties from the json data
        self.body_image_path = body_dict["body_image_path"]
        self.face_position = tuple(body_dict["face_position"])

        # Set the _color properties from the json data
        self.primary_colors = [
            tuple(color) for color in body_dict["primary_colors"]
        ]
        self.secondary_colors = [
            tuple(color) for color in body_dict["secondary_colors"]
        ]
        self.tertiary_colors = [
            tuple(color) for color in body_dict["tertiary_colors"]
        ]

        # Load the image files.
        if self.body_image_path:
            self.body_image = PILImage.open(self.body_image_path)
        if self.face_image_path:
            self.face_image = PILImage.open(self.face_image_path)

    def get_state(self) -> Optional[Mapping[str, Any]]:
        if self.name:
            return self.__dict__

        return None

    def set_state(self, save_data: Optional[Mapping[str, Any]]) -> None:
        # TODO: There's no point optimising this until Body is actually used.
        if save_data:
            for attr, value in save_data.items():
                setattr(self, attr, value)


def replace_color(
    image: Image,
    original_color: tuple[int, int, int],
    replacement_color: tuple[int, int, int],
) -> Image:
    """
    Replaces an RGB color in an image with a different RGB _color.

    Parameters:
        image: A PIL Image() object of the image to replace colors.
        original_color: A tuple of the RGB (r, g, b) value of the color to
            replace.
        replacement_color: A tuple of the RGB (r, g, b) value of the
            new color.

    Returns:
        A PIL Image() object of the image with the given colors replaced.

    """
    img = image.convert("RGBA")
    datas = list(img.getdata())

    r = original_color[0]
    g = original_color[1]
    b = original_color[2]

    new_r = replacement_color[0]
    new_g = replacement_color[1]
    new_b = replacement_color[2]

    newData = []
    for item in datas:
        if item[0] == r and item[1] == g and item[2] == b:
            newData.append((new_r, new_g, new_b, 255))
        else:
            newData.append(item)

    img.putdata(newData)

    return img


def fuse(
    body: Body,
    face: Body,
    save: bool = True,
    filename: Optional[str] = None,
) -> Image:
    """Fuses two sprites together given a body and a face.

    The resulting body will take on the colors of the face.

    Parameters:
        body: A Body() instance of the body that will be used in the end
            result.
        face: A Body() instance of the face that will be used in the end
            result.
        save: True or false value of whether or not to save the resulting
            fusion to a file.
        filename: If saving the result, specify the filename to save the
            resulting image.

    Returns:
        A PIL Image() object of the fused sprites.

    Example:

        >>> sapsnap = Body()
        >>> sapsnap.load('fusion/Sapsnap.json')
        >>>
        >>> vivitron = Body()
        >>> vivitron.load('fusion/Vivitron.json')
        >>>
        >>> # Fuse the sprites.
        >>> fuse(body=sapsnap, face=vivitron)
        >>> fuse(body=vivitron, face=sapsnap)


    """
    logger.info(
        f"Starting fusion for body '{body.name}' and face '{face.name}'."
    )
    logger.debug(
        f"Body size: {body.body_image.size}, mode: {body.body_image.mode}"
    )
    logger.debug(
        f"Face size: {face.face_image.size}, mode: {face.face_image.mode}"
    )

    color_mappings = get_color_mappings(body, face)
    logger.info("Replacing colors in body image...")
    body_image = replace_multiple_colors(body.body_image, color_mappings)

    logger.info("Resizing face image to match body's proportions...")
    new_face_image = resize_face_image(
        face.face_image, body.head_size, face.head_size
    )
    logger.debug(f"Resized face dimensions: {new_face_image.size}")

    logger.info("Calculating face position...")
    face_position = calculate_face_position(body, new_face_image)
    logger.debug(f"Calculated face position: {face_position}")

    logger.info("Pasting face image onto body image...")
    fused_image = paste_face_onto_body(
        body_image, new_face_image, face_position
    )

    if save:
        if not filename:
            filename = f"fusion/{body.prefix}{face.suffix}.png"
        logger.info(f"Saving fused image to file: {filename}.")
        fused_image.save(filename)
        logger.debug(f"Final fused image dimensions: {fused_image.size}")

    logger.info("Fusion process completed successfully!")
    return fused_image


def get_color_mappings(
    body: Body, face: Body
) -> list[tuple[tuple[int, int, int], tuple[int, int, int]]]:
    """
    Generates a list of color mappings that define the correspondence
    between the body's and face's primary, secondary, and tertiary colors
    for replacement.
    """
    color_mappings = (
        [
            (body.primary_colors[i], face.primary_colors[i])
            for i in range(len(body.primary_colors))
        ]
        + [
            (body.secondary_colors[i], face.secondary_colors[i])
            for i in range(len(body.secondary_colors))
        ]
        + [
            (body.tertiary_colors[i], face.tertiary_colors[i])
            for i in range(len(body.tertiary_colors))
        ]
    )
    return color_mappings


def replace_multiple_colors(
    image: Image,
    color_sets: list[tuple[tuple[int, int, int], tuple[int, int, int]]],
) -> Image:
    """
    Replaces multiple colors in an image based on a list of original
    and replacement color pairs.
    """
    for original_color, replacement_color in color_sets:
        image = replace_color(image, original_color, replacement_color)
    return image


def resize_face_image(
    face_image: Image,
    body_head_size: tuple[int, int],
    face_head_size: tuple[int, int],
) -> Image:
    """
    Resizes the face image proportionally to match the dimensions of
    the body's head.
    """
    ratio_x = float(body_head_size[0]) / float(face_head_size[0])
    ratio_y = float(body_head_size[1]) / float(face_head_size[1])
    new_size = (
        int(face_image.size[0] * ratio_x),
        int(face_image.size[1] * ratio_y),
    )
    return face_image.resize(new_size)


def calculate_face_position(body: Body, face_image: Image) -> tuple[int, int]:
    """
    Calculates the position where the face image should be pasted onto
    the body image, ensuring correct alignment.
    """
    return (
        int(body.face_position[0] - (face_image.size[0] / 2)),
        int(body.face_position[1] - (face_image.size[1] / 2)),
    )


def paste_face_onto_body(
    body_image: Image, face_image: Image, position: tuple[int, int]
) -> Image:
    """
    Pastes the resized face image onto the body image at the specified
    position, returning the modified body image.
    """
    body_image_copy = body_image.copy()
    body_image_copy.paste(face_image, position, face_image)
    return body_image_copy
