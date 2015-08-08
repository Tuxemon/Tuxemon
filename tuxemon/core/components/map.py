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
# core.components.map Game map module.
#
#

import logging
import pygame
import os
import sys

# PyTMX LOVES to change their API without notice. Here we try and handle that.
try:
    from pytmx import load_pygame
except ImportError:
    from pytmx.util_pygame import load_pygame

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)
logger.debug("components.map successfully imported")


class Map(object):
    """Maps are loaded from standard tmx files created from a map editor like Tiled. Events and
    collision regions are loaded and put in the appropriate data structures for the game to
    understand.

    **Tiled:** http://www.mapeditor.org/

    """
    def __init__(self, filename):
        self.filename = None
        self.data = None

        # Get the tile size from a tileset in our map. This is used to calculate the number of tiles
        # in a collision region.
        self.tile_size = (0, 0)

        # Collision tiles in tmx object format
        self.collisions = []
        
        self.events = []
        
        # Initialize the map
        self.load(filename)
        

    def load(self, filename):
        """Load map data from a tmx map file and get all the map's events and collision areas.
        Loading the map data is done using the pytmx library.

        Specifications for the TMX map format can be found here:
        https://github.com/bjorn/tiled/wiki/TMX-Map-Format
        
        :param filename: The path to the tmx map file to load.
        
        :type filename: String
    
        :rtype: None
        :returns: None 
        
        **Examples:**

        In each map, there are three types of objects: **collisions**, **conditions**, and
        **actions**. Here is how an action would be defined using the Tiled map editor:

        .. image:: images/map/map_editor_action01.png

        Here is an example of how we use pytmx to load the map data from a tmx file and what
        those objects would look like after loading:

        >>> tmx_data = pytmx.TiledMap("pallet_town-room.tmx")
        >>> for obj in tmx_data.objects:
        ...     pprint.pprint(obj.__dict__)
        ...
        {'gid': 0,
         'height': 32,
         'name': None,
         'parent': <TiledMap: "../tuxemon/resources/maps/pallet_town-room.tmx">,
         'rotation': 0,
         'type': 'collision',
         'visible': 1,
         'width': 16,
         'x': 160,
         'y': 48}
        {'action_id': '9',
         'condition_type': 'player_at',
         'gid': 0,
         'height': 16,
         'id': 9,
         'name': 'Start Combat',
         'operator': 'is',
         'parameters': '1,11',
         'parent': <TiledMap: "../tuxemon/resources/maps/pallet_town-room.tmx">,
         'rotation': 0,
         'type': 'condition',
         'visible': 1,
         'width': 16,
         'x': 16,
         'y': 176}
        {'action_type': 'teleport',
         'gid': 0,
         'height': 16,
         'id': 5,
         'name': 'Go Downstairs',
         'parameters': 'test.tmx,5,5',
         'parent': <TiledMap: "../tuxemon/resources/maps/pallet_town-room.tmx">,
         'priority': '1',
         'rotation': 0,
         'type': 'action',
         'visible': 1,
         'width': 16,
         'x': 0,
         'y': 0}

        """
        
        # Load the tmx map data using the pytmx library.
        self.filename = filename
        #self.data = pytmx.TiledMap(filename)
        self.data = load_pygame(filename, pixelalpha=True)
        
        # Get the map dimensions
        self.size = (self.data.width, self.data.height)

        # Get the tile size of the map
        self.tile_size = (self.data.tilesets[0].tilewidth, self.data.tilesets[0].tileheight)

        # Load all objects from the map file and sort them by their type.
        for obj in self.data.objects:
            if obj.type == 'collision':
                self.collisions.append(obj)

            elif obj.type == 'event':
                conds = []
                acts = []
                
                # Conditions & actions are stored as Tiled properties.
                # We need to sort them by name, so that "act1" comes before "act2" and so on..
                keys = sorted(obj.properties.keys())
                
                for k in keys:
                    if k.startswith('cond'):
                        words = obj.properties[k].split(' ', 2)
                        
                        # Conditions have the form 'operator type parameters'.
                        operator, type = words[0:2]
                        
                        args = ''
                        if len(words) > 2:
                            args = words[2]
                        
                        conds.append({
                            'type': type,
                            'parameters': args,
                            'x': int(obj.x / self.tile_size[0]),
                            'y': int(obj.y / self.tile_size[1]),
                            'width': int(obj.width / self.tile_size[0]),
                            'height': int(obj.height / self.tile_size[1]),
                            'operator': operator
                        })
                    elif k.startswith('act'):
                        acts.append(obj.properties[k].split(' ', 1))
                
                self.events.append({'conds':conds, 'acts':acts})


    def loadfile(self, tile_size):
        """Loads the tile and collision data from the map file and returns a list of tiles with
        their position and pygame surface, a set of collision tile coordinates, and the size of
        the map itself. The list of tile surfaces is used to draw the map in the main game. The 
        list of collision tile coordinates is used for collision detection.
        
        :param tile_size: An [x, y] size of each tile in pixels AFTER scaling. This is used for
            scaling and positioning.
        
        :type tile_size: List
    
        :rtype: List
        :returns: A multi-dimensional list of tiles in dictionary format; a set of collision
            coordinates; the map size.

        **Examples:**

        The list of tiles is structured in a way where you can access an individual tile by
        index number. For example, to get a tile located at (2, 1), you can access the tile's
        details using:

        >>> x = 2
        >>> y = 1
        >>> layer = 0
        >>> tiles[x][y][layer]

        Here is an example of what the the tiles list data structure actually looks like:

        >>> tiles, collisions, mapsize =  map.loadfile([24, 24])
        >>> tiles
            [
              [
                [], 
                [], 
                [], 
                [], 
                [], 
                [], 
                [], 
                [], 
                [], 
                [], 
                []
              ],
              [ [],
                [{'layer': 1,
                'name': '6,0',
                'position': (80, 80),
                'surface': <Surface(16x16x32 SW)>,
                'tile_pos': [1, 1],
                'tileset': 'resources/gfx/tileset.png'}],
                [{'layer': 1,
                'name': '7,0',
                'position': (80, 160),
                'surface': <Surface(16x16x32 SW)>,
                'tile_pos': [1, 2],
                'tileset': 'resources/gfx/tileset.png'}],
                [{'layer': 1,
                'name': '8,0',
                'position': (80, 240),
                'surface': <Surface(16x16x32 SW)>,
                'tile_pos': [1, 3],
                'tileset': 'resources/gfx/tileset.png'}],
                [{'layer': 1,
                'name': '9,0',
                'position': (80, 320),
                'surface': <Surface(16x16x32 SW)>,
                'tile_pos': [1, 4],
                'tileset': 'resources/gfx/tileset.png'}],
                [{'layer': 1,
                'name': '9,0',
                'position': (80, 400),
                'surface': <Surface(16x16x32 SW)>,
                'tile_pos': [1, 5],
                'tileset': 'resources/gfx/tileset.png'},            
                {'layer': 3,
                'name': '10,0',
                'position': (80, 400),
                'surface': <Surface(16x16x32 SW)>,
                'tile_pos': [1, 5],
                'tileset': 'resources/gfx/tileset.png'}],
        ...


        The collision map is a set of (x,y) coordinates that the player cannot walk
        through. This set is generated based on collision regions defined in the
        map file.

        Here is an example of what the collision set looks like:

        >>> tiles, collisions, mapsize =  map.loadfile([24, 24])
        >>> collisions
        set([(0, 2),
             (0, 3),
             (0, 4),
             (0, 5),
             (0, 6)])

        """ 

        # Create a list of all of the tiles in the map
        tiles = []

        # Loop through all tiles in our map file and get the pygame surface associated with it.
        for x in range(0, self.data.width):
            
            # Create a list of tile for the y-axis
            y_list = []

            for y in range(0, self.data.height):
                
                layer_list = []

                # Get the number of tile layers.
                num_of_layers = 0

                # PyTMX recently changed some of their attribute names.
                # This ensures we get the number of layers regardless of
                # the version of PyTMX.
                try:
                    for layer in self.data.layers:
                        if hasattr(layer, 'data'):
                            num_of_layers += 1
                except AttributeError:
                    for layer in self.data.tilelayers:
                        num_of_layers += 1

                # Get all the map tiles for each layer
                for layer in range(0, num_of_layers):

                    # PyTMX recently changed their method names. This
                    # ensures the map will load regardless of the PyTMX
                    # version.
                    try:
                        surface = self.data.getTileImage(x, y, layer)
                    except AttributeError:
                        surface = self.data.get_tile_image(x, y, layer)
                    
                    # Create a tile based on the image
                    if surface:
                        tile = {'tile_pos': (x, y),
                                'position': (x * tile_size[0], y * tile_size[1]),
                                'layer': layer + 1,
                                'name': str(x) + "," + str(y),
                                'surface': surface
                                }
                        
                        layer_list.append(tile)
                        
                y_list.append(layer_list)
                
            tiles.append(y_list)

        # Get the dimensions of the map
        mapsize = self.size

        # Create a list of all tile positions that we cannot walk through
        collision_map = set()

        # Right now our collisions are defined in our tmx file as large regions that the player
        # can't pass through. We need to convert these areas into individual tile coordinates
        # that the player can't pass through.
        # Loop through all of the collision objects in our tmx file.
        for collision_region in self.collisions:

            # >>> collision_region.__dict__
            #{'gid': 0,
            # 'height': 16,
            # 'name': None,
            # 'parent': <TiledMap: "resources/maps/pallet_town-room.tmx">,
            # 'rotation': 0,
            # 'type': 'collision',
            # 'visible': 1,
            # 'width': 16,
            # 'x': 176,
            # 'y': 64}


            # Get the collision area's tile location and dimension in tiles using the tileset's
            # tile size.
            x = self.round_to_divisible(collision_region.x, self.tile_size[0]) / self.tile_size[0]
            y = self.round_to_divisible(collision_region.y, self.tile_size[1]) / self.tile_size[1]
            width = self.round_to_divisible(collision_region.width, self.tile_size[0]) / self.tile_size[0]
            height = self.round_to_divisible(collision_region.height, self.tile_size[1]) / self.tile_size[1]

            # Loop through the area of this region and create all the tile coordinates that are 
            # inside this region.
            for a in range(0, int(width)):
                for b in range(0, int(height)):
                    collision_tile = (a + x, b + y)
                    collision_map.add(collision_tile)

        return tiles, collision_map, mapsize

    def round_to_divisible(self, x, base=16):
        """Rounds a number to a divisible base. This is used to round collision areas that aren't
        defined well. This function assists in making sure collisions work if the map creator
        didn't set the collision areas to round numbers.

        :param x: The number we want to round.
        :param base: The base that we want our number to be divisible by. (Default: 16)

        :type x: Float
        :type base: Integer

        :rtype: Integer
        :returns: Rounded number that is divisible by "base".

        **Examples:**

        >>> round_to_divisible(31.23, base=16)
        32
        >>> round_to_divisible(17.8, base=16)
        16

        """
        return int(base * round(float(x)/base))


class Tile(object):
    """A class to create tile objects. Tile objects are used to keep track of tile properties such
    as the layer it's on, its position, surface, and other properties.

    """
    def __init__(self, name, surface, tileset):
        self.name = name
        self.surface = surface
        self.layer = None
        self.type = None
        self.tileset = tileset

# If the module is being run as a standalone program, run an example
if __name__=="__main__":
    
    from . import config
    
    # set up pygame 
    pygame.init()

    # read the configuration file
    config = config.Config()

    # The game resolution
    resolution = config.resolution
    
    # set up the window with epic name
    screen = pygame.display.set_mode(resolution, config.fullscreen, 32)
    pygame.display.set_caption('Tuxemon Map')
    
    # Native resolution is similar to the old gameboy resolution. This is used for scaling.
    native_resolution = [240, 160]
    
    # If scaling is enabled, scale the tiles based on the resolution
    if config.scaling == "1":
        scale = int( (resolution[0] / native_resolution[0]) )
        
    # Fill background
    background = pygame.Surface(screen.get_size())
    background = background.convert()
    background.fill((0, 0, 0))

    # Blit everything to the screen
    screen.blit(background, (0, 0))
    pygame.display.flip()
    
    print "Loading map"
    tile_size = [80, 80]    # 1 tile = 16 pixels
    testmap = Map()
    testmap.loadfile("resources/maps/test.map", tile_size)

    # Event loop THIS IS WHAT SHIT IS DOING RIGHT NOW BRAH
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                sys.exit()
            
            # Exit the game if you press ESC
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit()
                

        screen.blit(background, (0, 0))
        pygame.display.flip()
