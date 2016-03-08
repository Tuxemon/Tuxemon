#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Tuxemon
# Copyright (C) 2014, William Edwards <shadowapex@gmail.com>,
#                     Benjamin Bean <superman2k5@gmail.com>
#
# This file is part of Tuxemon.
#
# Tuxemon is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Tuxemon is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Tuxemon.  If not, see <http://www.gnu.org/licenses/>.
#
# Contributor(s):
#
# William Edwards <shadowapex@gmail.com>
#
# core.components.fusion Module to fuse the face and body of two sprites.
#               Based on Pokemon Fusion by Alex Onsager
#               http://www.alexonsager.net/blog/2013/06/04/behind-the-scenes-pokemon-fusion/
#

try:
    from PIL import Image
except ImportError:
    pass
import json, pprint


class Body(object):
    """A class that holds sprite, _color, and face position data for use with fusing two sprites
    together.

    :param: None

    **Example:**

    >>> bulbasaur = Body()
    >>> bulbasaur.load('fusion/Bulbasaur.json') # Load the sprite data from a json file
    >>>
    >>> gyarados = Body()
    >>> gyarados.load('fusion/Gyarados.json')   # Load the sprite data from a json file
    >>>
    >>> # Fuse the sprites.
    >>> fuse(body=bulbasaur, face=gyarados)
    >>> fuse(body=gyarados, face=bulbasaur)

    """

    def __init__(self):

        # Name properties
        self.prefix = ""            # A name prefix to use when fusing sprites
        self.suffix = ""            # A name suffix to use when fusing sprites
        self.name = ""              # The full name of the sprite when you concat prefix + suffix

        # Face Properties
        self.face_image_path = ""   # The path to the face image to use.
        self.face_image = ""

        self.face_size = (0, 0)     # The face size can be automatically obtained through self.get_face_size()
        self.head_size = (0, 0)     # The head size differs from the face size to take beaks, etc. into account.
        self.face_center = (0, 0)   # The center of the face.


        # Body properties
        self.body_image_path = ""   # The path to the body image to use.
        self.body_image = ""
        self.face_position = (0, 0) # The center of the face on the body.

        # Colors
        self.primary_colors = [(0,0,0), (0,0,0), (0,0,0), (0,0,0), (0,0,0)]     # 5 primary colors of the sprite
        self.secondary_colors = [(0,0,0), (0,0,0), (0,0,0), (0,0,0), (0,0,0)]   # 5 secondary colors of the sprite
        self.tertiary_colors= [(0,0,0), (0,0,0), (0,0,0), (0,0,0), (0,0,0)]     # 5 tertiary colors of the sprite


    def get_face_size(self):
        """Obtains the size of the face image in pixels and sets the instance's face_size to the returned value.

        :param: None

        :rtype: Tuple
        :returns: A tuple (x, y) of the face size in pixels.

        """

        img = self.face_image
        img = img.convert("RGBA")
        self.face_size = img.getdata().size

        return self.face_size


    def to_json(self):
        """Converts the current instance to a dictionary and converts it to json format.

        :param: None

        :rtype: String
        :returns: A json string of the current instance.

        """

        body_dict = self.__dict__
        del body_dict['body_image']
        del body_dict['face_image']

        return json.dumps(body_dict)


    def save(self, filename=None):
        """Saves the current instance and all its properties to a file containing json text.

        :param filename: The path to the file to save.

        :type filename: String

        :rtype: None
        :returns: None

        """

        if not filename:
            filename = "fusion/%s.json" % self.name

        output = self.to_json()
        f = open(filename, "w")
        f.write(output)
        f.close()


    def load(self, json_data, file=True):
        """Loads and sets all of the properties of this instance to the properties contained within
        a json string or file.

        :param json_data: The string of json text or the file path to a json file to load.
        :param file: True or false value of whether or not "json_data" is a file path.

        :type json_data: String
        :type file: Boolean

        :rtype: None
        :returns: None

        **Example:**

        >>> bulbasaur = Body()
        >>> bulbasaur.load('fusion/Bulbasaur.json')

        """

        # If "file" is set to true, then assume that json_data is a path to a file containing json.
        if file:
            f = open(json_data, 'r')
            json_data = ''.join(f.readlines())
            f.close()

        # Load the json data and convert it to a dictionary.
        body_dict = json.loads(json_data)

        # Set the name from the json data
        self.prefix = body_dict["prefix"]
        self.suffix = body_dict["suffix"]
        self.name = body_dict["name"]

        # Set the face properties from the json data
        self.face_image_path =  body_dict["face_image_path"]
        self.face_size =  body_dict["face_size"]
        self.head_size =  body_dict["head_size"]
        self.face_center =  body_dict["face_center"]

        # Set the body properties from the json data
        self.body_image_path =  body_dict["body_image_path"]
        self.face_position =  body_dict["face_position"]

        # Set the _color properties from the json data
        self.primary_colors =  body_dict["primary_colors"]
        self.secondary_colors =  body_dict["secondary_colors"]
        self.tertiary_colors =  body_dict["tertiary_colors"]

        # Load the image files.
        self.body_image = Image.open(self.body_image_path)
        self.face_image = Image.open(self.face_image_path)



def replace_color(image, original_color, replacement_color):
    """Replaces an RGB _color in an image with a different RGB _color.

    :param image: A PIL Image() object of the image to replace colors.
    :param original_color: A tuple of the RGB (r, g, b) value of the _color to replace.
    :param replacement_color: A tuple of the RGB (r, g, b) value of the new _color.

    :type image: PIL.Image
    :type original_color: Tuple
    :type replacement_color: Tuple

    :rtype: PIL.Image
    :returns: A PIL Image() object of the image with the given colors replaced.

    """


    img = image.convert("RGBA")
    datas = img.getdata()

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




def fuse(body, face, save=True, filename=None):
    """Fuses two sprites together given a body and a face. The resulting body will take on the
    colors of the face.

    :param body: A Body() instance of the body that will be used in the end result.
    :param face: A Body() instance of the face that will be used in the end result.
    :param save: True or false value of whether or not to save the resulting fusion to a file.
    :param filename: If saving the result, specify the filename to save the resulting image.

    :type body: fusion.Body
    :type face: fusion.Body
    :type save: Boolean
    :type filename: String

    :rtype: PIL.Image
    :returns: A PIL Image() object of the fused sprites.

    **Example:**

    >>> bulbasaur = Body()
    >>> bulbasaur.load('fusion/Bulbasaur.json')
    >>>
    >>> gyarados = Body()
    >>> gyarados.load('fusion/Gyarados.json')
    >>>
    >>> # Fuse the sprites.
    >>> fuse(body=bulbasaur, face=gyarados)
    >>> fuse(body=gyarados, face=bulbasaur)


    """

    # Create a working copy of the body image so we don't alter the original sprite.
    body_image = body.body_image.copy()

    # Replace the _color of the body with the colors of the face.
    for i, color in enumerate(body.primary_colors):
        body_image = replace_color(body_image, body.primary_colors[i], face.primary_colors[i])
        body_image = replace_color(body_image, body.secondary_colors[i], face.secondary_colors[i])
        body_image = replace_color(body_image, body.tertiary_colors[i], face.tertiary_colors[i])

    # Set a scale for the images so we can resize them. Scaling results in a better image result.
    scale = 4

    # Scale the images
    body_image = body_image.resize(
        (body_image.getdata().size[0] * scale, body_image.getdata().size[1] * scale))
    face.face_image = face.face_image.resize(
        (face.face_image.getdata().size[0] * scale, face.face_image.getdata().size[1] * scale))

    # Update face size after we've performed our scaling.
    face.face_size = (face.face_image.getdata().size[0], face.face_image.getdata().size[1])

    # Scale the new face position.
    body.face_position = (
        ((body.face_position[0]-1) * scale)+1, ((body.face_position[1]-1) * scale)+1)

    # Compare the head size of the body and the face so we can scale the face to fit the body.
    ratio_x = float(body.head_size[0]) / float(face.head_size[0])
    ratio_y = float(body.head_size[1]) / float(face.head_size[1])

    # Resize the head in ratio with the head size of the body
    new_size = (int(face.face_image.getdata().size[0] * ratio_x), int(
        face.face_image.getdata().size[1] * ratio_y))
    face.face_image = face.face_image.resize(new_size)

    face.face_size = (face.face_image.getdata().size[0], face.face_image.getdata().size[1])

    # Paste the face onto the body
    position = (body.face_position[0] - \
        (face.face_size[0]/2), body.face_position[1] - (face.face_size[1]/2))
    body_image.paste(face.face_image, position, face.face_image)


    # For some reason this looks really good.
    # Scale the image back down using Image.ANTIALIAS
    x = body_image.getdata().size[0] / (scale / 2)
    y = body_image.getdata().size[1] / (scale / 2)
    newsize = (x, y)
    body_image = body_image.resize(newsize, Image.ANTIALIAS)

    # Scale the image down further to its original size without ANTIALIAS
    x /= (scale / 2)
    y /= (scale / 2)
    newsize = (x, y)
    body_image = body_image.resize(newsize)

    # Save the resulting image
    if save:
        if not filename:
            filename = "fusion/%s%s.png" % (body.prefix, face.suffix)
        body_image.save(filename)

    return body_image


