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
#
# core.components.screen Used to handle panning of the screen.
#
#

import logging
import pygame

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)
logger.debug("%s successfully imported" % __name__)


def pan_left(global_x, pps, time_passed_seconds, limit_x=0):
    """Pans the screen to the left by adding to the global_x variable

    :param global_x: -- The main global_x variable used to modify the coordinates of all
        panable objects
    :param pps: -- The paning rate specified in pixels per second
    :param time_passed_seconds: -- The amount of time passed in seconds between this frame and
        the last frame
    :param limit_x: [optional] Optional limit_x value that prevents panning over this specified
        limit

    :type global_x: Integer
    :type pps: Integer
    :type time_passed_seconds: Float
    :type limit_x: Integer

    :rtype: Integer
    :returns: The modified global_x variable

    """
    # Set the number of pixels that we'll pan based on how much time has passed since the last frame.
    pan_x = pps * time_passed_seconds
    # Check to see if we will exceed the limit if we add the pan_x to the global_x
    if (global_x + pan_x) < limit_x:
        global_x += pan_x
    # If it is, just set the global_x to the limit itself so it doesn't go over.
    else:
        global_x = limit_x

    return global_x

def pan_right(global_x, pps, time_passed_seconds, limit_x):
    """Pans the screen to the right by subtracting from the global_x variable

    :param global_x: -- The main global_x variable used to modify the coordinates of all panable
        objects
    :param pps: -- The paning rate specified in pixels per second
    :param time_passed_seconds: -- The amount of time passed in seconds between this frame and the
        last frame
    :param limit_x: [optional] Optional limit_x value that prevents panning over this specified
        limit

    :type global_x: Integer
    :type pps: Integer
    :type time_passed_seconds: Float
    :type limit_x: Integer

    :rtype: Integer
    :returns: The modified global_x variable

    """
    #print("Start paning right!")
    pan_x = pps * time_passed_seconds

    # Check to see if we will exceed the limit if we add the pan_x to the global_x
    # If it is, just set the global_x to the limit itself.
    if (global_x - pan_x) > limit_x:
        global_x -= pan_x
    else:
        global_x = limit_x

    return global_x

def pan_up(global_y, pps, time_passed_seconds, limit_y=0):
    """Pans the screen up by adding to the global_y variable

    :param global_y: The main global_y variable used to modify the coordinates of all panable
        objects
    :param pps: The paning rate specified in pixels per second
    :param time_passed_seconds: The amount of time passed in seconds between this frame and the
        last frame
    :param limit_y: [optional] limit_y value that prevents panning over this specified limit

    :type global_y: Integer
    :type pps: Integer
    :type time_passed_seconds: Float
    :type limit_y: Integer

    :rtype: Integer
    :returns: The modified global_y variable

    """
    #print("Start paning up!")
    pan_y = pps * time_passed_seconds

    # Check to see if we will exceed the limit if we add the pan_x to the global_x
    # If it is, just set the global_x to the limit itself so it doesn't go over.
    if (global_y + pan_y) < limit_y:
        global_y += pan_y
    else:
        global_y = limit_y

    return global_y

def pan_down(global_y, pps, time_passed_seconds, limit_y):
    """Pans the screen down by subtracting from the global_y variable

    :param global_y: The main global_y variable used to modify the coordinates of all panable
        objects
    :param pps: The paning rate specified in pixels per second
    :param time_passed_seconds: The amount of time passed in seconds between this frame and the
        last frame
    :param limit_y: [optional] limit_y value that prevents panning over this specified limit

    :type global_y: Integer
    :type pps: Integer
    :type time_passed_seconds: Float
    :type limit_y: Integer

    :rtype: Integer
    :returns: The modified global_y variable

    """
    #print("Start paning down!")
    pan_y = pps * time_passed_seconds

    # Check to see if we will exceed the limit if we add the pan_x to the global_x
    # If it is, just set the global_x to the limit itself.
    if (global_y - pan_y) > limit_y:
        global_y -= pan_y
    else:
        global_y = limit_y

    return global_y

def mouse_pan_left(mouse_pos, pan_margin, global_x, pps, time_passed_seconds, limit_x=0):
    """Pans the screen left by adding to the global_x variable based on if the mouse position
    is within the specified pan margin

    :param mouse_pos: The current mouse position in tuple format (e.g. (25, 40) )
    :param pan_margin: Value in pixels of margin of the screen that the mouse must be within
        in order to start panning
    :param global_x: The main global_x variable used to modify the coordinates of all panable
        objects
    :param pps: The paning rate specified in pixels per second
    :param time_passed_seconds: The amount of time passed in seconds between this frame and the
        last frame
    :param limit_x: [optional] limit_x value that prevents panning over this specified limit

    :type mouse_pos: Tuple
    :type pan_margin: Integer
    :type global_x: Integer
    :type pps: Integer
    :type time_passed_seconds: Float
    :type limit_x: Integer

    :rtype: Integer
    :returns: The modified global_x variable

    """
    # Handle paning left
    if mouse_pos[0] < pan_margin and global_x < limit_x:
        return pan_left(global_x, pps, time_passed_seconds)

    else:
        return global_x

def mouse_pan_right(mouse_pos, pan_margin, global_x, pps, time_passed_seconds, resolution, limit_x):
    """Pans the screen right by subtracting from the global_x variable based on if the mouse position
    is within the specified pan margin

    :param mouse_pos: The current mouse position in tuple format (e.g. (25, 40) )
    :param pan_margin: Value in pixels of margin of the screen that the mouse must be within in
        order to start panning
    :param global_x: The main global_x variable used to modify the coordinates of all panable
        objects
    :param pps: The paning rate specified in pixels per second
    :param time_passed_seconds: The amount of time passed in seconds between this frame and the
        last frame
    :param limit_x: [optional] limit_x value that prevents panning over this specified limit

    :type mouse_pos: Tuple
    :type pan_margin: Integer
    :type global_x: Integer
    :type pps: Integer
    :type time_passed_seconds: Float
    :type limit_x: Integer

    :rtype: Integer
    :returns: The modified global_x variable

    """
    if mouse_pos[0] > resolution[0] - pan_margin and global_x > limit_x:
        return pan_right(global_x, pps, time_passed_seconds, limit_x)

    else:
        return global_x

def mouse_pan_up(mouse_pos, pan_margin, global_y, pps, time_passed_seconds, limit_y=0):
    """Pans the screen up by adding to the global_y variable based on if the mouse position
    is within the specified pan margin

    :param mouse_pos: The current mouse position in tuple format (e.g. (25, 40) )
    :param pan_margin: Value in pixels of margin of the screen that the mouse must be within in
        order to start panning
    :param global_y: The main global_y variable used to modify the coordinates of all panable
        objects
    :param pps: The paning rate specified in pixels per second
    :param time_passed_seconds: The amount of time passed in seconds between this frame and the
        last frame
    :param limit_y: [optional] limit_y value that prevents panning over this specified limit

    :type mouse_pos: Tuple
    :type pan_margin: Integer
    :type global_y: Integer
    :type pps: Integer
    :type time_passed_seconds: Float
    :type limit_y: Integer

    :rtype: Integer
    :returns: The modified global_y variable

    """
    # Handle paning up
    if mouse_pos[1] < pan_margin and global_y < limit_y:
        return pan_up(global_y, pps, time_passed_seconds)

    else:
        return global_y


def mouse_pan_down(mouse_pos, pan_margin, global_y, pps, time_passed_seconds, resolution, limit_y):
    """Pans the screen down by subtracting from the global_y variable based on if the mouse position
    is within the specified pan margin

    :param mouse_pos: The current mouse position in tuple format (e.g. (25, 40) )
    :param pan_margin: Value in pixels of margin of the screen that the mouse must be within in
        order to start panning
    :param global_y: The main global_y variable used to modify the coordinates of all panable
        objects
    :param pps: The paning rate specified in pixels per second
    :param time_passed_seconds: The amount of time passed in seconds between this frame and the
        last frame
    :param limit_y: [optional] limit_y value that prevents panning over this specified limit

    :type mouse_pos: Tuple
    :type pan_margin: Integer
    :type global_y: Integer
    :type pps: Integer
    :type time_passed_seconds: Float
    :type limit_y: Integer

    :rtype: Integer
    :returns: The modified global_y variable

    """
    if mouse_pos[1] > resolution[1] - pan_margin and global_y > limit_y:
        return pan_down(global_y, pps, time_passed_seconds, limit_y)

    else:
        return global_y


def center_map(tile_size, map_size, resolution):
    """ Centers the map and resets the panning limit

    :param tile_size: The map tile size in pixels as a list of [x,y] pixels.
    :param map_size: The map size in number of tiles as a list of [x,y] tiles.
    :param resolution: The resolution as a list of [x,y] in pixels.

    :type tile_size: List
    :type map_size: List
    :type resolution: List

    :rtype: Tuple
    :returns: A tuple with the (limit_x, limit_y, global_x, global_y)

    """

    # Set the new panning limit based on the new map size.
    limit_x = -( (tile_size[0] * map_size[0]) - resolution[0])
    limit_y = -( (tile_size[1] * map_size[1]) - resolution[1])

    # Center the map
    global_x = limit_x / 2
    global_y = limit_y / 2

    return limit_x, limit_y, global_x, global_y


def blit_alpha(target, source, location, opacity):
    """ Blits a surface with alpha that can also have it's overall transparency modified
    Taken from http://nerdparadise.com/tech/python/pygame/blitopacity/

    :param target: The target surface to blit the image to. This is usually the screen or some
        other subsurface.
    :param source: The source surface that you wish to blit with transparency.
    :param location: A tuple of the coordinates where you wish to blit the image.
    :param opacity: The transparency level you wish the overall image to have.

    :type target: pygame.Surface
    :type source: pygame.Surface
    :type location: Tuple
    :type opacity: Integer

    :rtype: None
    :returns: None

    """

    x = location[0]
    y = location[1]
    temp = pygame.Surface((source.get_width(), source.get_height())).convert()
    temp.blit(target, (-x, -y))
    temp.blit(source, (0, 0))
    temp.set_alpha(opacity)
    target.blit(temp, location)
