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
# Leif Theden <leif.theden@gmail.com>
#
#
from __future__ import division

import math

import pygame
from pygame.transform import rotozoom
from pygame.transform import scale

from core.components.pyganim import PygAnimation


class Sprite(pygame.sprite.DirtySprite):
    dirty = False

    def __init__(self, *args, **kwargs):
        super(Sprite, self).__init__(*args, **kwargs)
        self.visible = True
        self._rotation = 0
        self._image = None
        self._original_image = None
        self._width = 0
        self._height = 0
        self._needs_rescale = False
        self._needs_update = False

    def draw(self, surface, rect=None):
        """ Draw the sprite to the surface

        This operation does not scale the sprite, so it may exceed
        the size of the area passed.

        :param surface: Surface to be drawn on
        :param rect: Area to contain the sprite
        :return: Area of the surface that was modified
        :rtype: pygame.rect.Rect
        """
        # should draw to surface without generating a cached copy
        if rect is None:
            rect = surface.get_rect()
        return self._draw(surface, rect)

    def _draw(self, surface, rect):
        return surface.blit(self._image, rect)

    @property
    def image(self):
        # should always be a cached copy
        if self._needs_update:
            self.update_image()
            self._needs_update = False
            self._needs_rescale = False
        return self._image

    @image.setter
    def image(self, image):
        if image is None:
            self._original_image = None
            return

        if hasattr(self, 'rect'):
            self.rect.size = image.get_size()
        else:
            self.rect = image.get_rect()
        self._original_image = image
        self._needs_update = True

    def update_image(self):
        if self._needs_rescale:
            w = self.rect.width if self._width is None else self._width
            h = self.rect.height if self._height is None else self._height
            image = scale(self._original_image, (w, h))
            center = self.rect.center
            self.rect.size = w, h
            self.rect.center = center
        else:
            image = self._original_image

        if self._rotation:
            image = rotozoom(image, self._rotation, 1)
            rect = image.get_rect(center=self.rect.center)
            self.rect.size = rect.size
            self.rect.center = rect.center

        self._width, self._height = self.rect.size
        self._image = image

    # width and height are API that may not stay
    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, width):
        width = int(round(width, 0))
        if not width == self._width:
            self._width = width
            self._needs_rescale = True
            self._needs_update = True

    # width and height are API that may not stay
    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, height):
        height = int(round(height, 0))
        if not height == self._height:
            self._height = height
            self._needs_rescale = True
            self._needs_update = True

    @property
    def rotation(self):
        return self._rotation

    @rotation.setter
    def rotation(self, value):
        value = int(round(value, 0)) % 360
        if not value == self._rotation:
            self._rotation = value
            self._needs_update = True


class SpriteGroup(pygame.sprite.LayeredUpdates):
    """ Sane variation of a pygame sprite group

    Features:
    * Supports Layers
    * Supports Index / Slice
    * Supports skipping sprites without an image
    * Supports sprites with visible flag
    * Get bounding rect of all children

    Variations from standard group:
    * SpriteGroup.add no longer accepts a sequence, use SpriteGroup.extend
    """
    _init_rect = pygame.Rect(0, 0, 0, 0)

    def __init__(self, *args, **kwargs):
        self._spritelayers = dict()
        self._spritelist = list()
        pygame.sprite.AbstractGroup.__init__(self)
        self._default_layer = kwargs.get('default_layer', 0)

    def __nonzero__(self):
        return bool(self._spritelist)

    def __getitem__(self, item):
        # patch in indexing / slicing support
        return self._spritelist.__getitem__(item)

    def draw(self, surface):
        spritedict = self.spritedict
        surface_blit = surface.blit
        dirty = self.lostsprites
        self.lostsprites = []
        dirty_append = dirty.append

        for s in self.sprites():
            if getattr(s, "image", None) is None:
                continue

            if not getattr(s, 'visible', True):
                continue

            if isinstance(s.image, PygAnimation):
                s.image.blit(surface, s.rect)
                continue

            r = spritedict[s]
            newrect = surface_blit(s.image, s.rect)
            if r:
                if newrect.colliderect(r):
                    dirty_append(newrect.union(r))
                else:
                    dirty_append(newrect)
                    dirty_append(r)
            else:
                dirty_append(newrect)
            spritedict[s] = newrect
        return dirty

    def extend(self, sprites, **kwargs):
        """ Add a sequence of sprites to the SpriteGroup

        :param sprites: Sequence (list, set, etc)
        :param kwargs:
        :returns: None
        """
        if '_index' in kwargs.keys():
            raise KeyError
        for index, sprite in enumerate(sprites):
            kwargs['_index'] = index
            self.add(sprite, **kwargs)

    def add(self, sprite, **kwargs):
        """ Add a sprite to group.  do not pass a sequence or iterator

        LayeredUpdates.add(*sprites, **kwargs): return None
        If the sprite you add has an attribute _layer, then that layer will be
        used. If **kwarg contains 'layer', then the passed sprites will be
        added to that layer (overriding the sprite._layer attribute). If
        neither the sprite nor **kwarg has a 'layer', then the default layer is
        used to add the sprites.
        """
        layer = kwargs.get('layer')
        if isinstance(sprite, pygame.sprite.Sprite):
            if not self.has_internal(sprite):
                self.add_internal(sprite, layer)
                sprite.add_internal(self)
        else:
            raise TypeError

    def calc_bounding_rect(self):
        """A rect object that contains all sprites of this group
        """
        sprites = self.sprites()
        if not sprites:
            return self.rect
        elif len(sprites) == 1:
            return pygame.Rect(sprites[0].rect)
        else:
            return sprites[0].rect.unionall([s.rect for s in sprites[1:]])


class RelativeGroup(SpriteGroup):
    """
    Drawing operations are relative to the group's rect
    """
    rect = pygame.Rect(0, 0, 0, 0)

    def __init__(self, **kwargs):
        self.parent = kwargs.get('parent')
        super(RelativeGroup, self).__init__(**kwargs)

    def calc_bounding_rect(self):
        """A rect object that contains all sprites of this group
        """
        rect = super(RelativeGroup, self).calc_bounding_rect()
        for sprite in self.sprites():
            print sprite, sprite.rect
        return rect
        return self.calc_absolute_rect(rect)

    def calc_absolute_rect(self, rect):
        self.update_rect_from_parent()
        return rect.move(self.rect.topleft)

    def update_rect_from_parent(self):
        try:
            self.rect = self.parent()
        except TypeError:
            self.rect = pygame.Rect(self.parent.rect)

    def draw(self, surface):
        self.update_rect_from_parent()
        topleft = self.rect.topleft

        spritedict = self.spritedict
        surface_blit = surface.blit
        dirty = self.lostsprites
        self.lostsprites = []
        dirty_append = dirty.append

        for s in self.sprites():
            if s.image is None:
                continue

            if not getattr(s, 'visible', True):
                continue

            r = spritedict[s]
            newrect = surface_blit(s.image, s.rect.move(topleft))
            if r:
                if newrect.colliderect(r):
                    dirty_append(newrect.union(r))
                else:
                    dirty_append(newrect)
                    dirty_append(r)
            else:
                dirty_append(newrect)
            spritedict[s] = newrect
        return dirty


class VisualSpriteList(RelativeGroup):
    """
    Sprite group which can be configured to arrange the children
    sprites into columns.
    """
    orientation = 'horizontal'  # default, and only implemented
    expand = True               # will fill all space of parent, if false, will be more compact

    def __init__(self, **kwargs):
        super(VisualSpriteList, self).__init__(**kwargs)
        self._needs_arrange = False
        self._columns = 1
        self.line_spacing = None

    @property
    def columns(self):
        return self._columns

    @columns.setter
    def columns(self, value):
        self._columns = value
        self._needs_arrange = True

    def calc_bounding_rect(self):
        if self._needs_arrange:
            self.arrange_menu_items()
            self._needs_arrange = False
        return super(VisualSpriteList, self).calc_bounding_rect()

    def add(self, item, **kwargs):
        """Add something to the stacker
        do not add iterables to this function.  use 'extend'
        :param item: stuff to add
        :returns: None
        """
        super(VisualSpriteList, self).add(item, **kwargs)
        self._needs_arrange = True

    def remove(self, *items):
        super(VisualSpriteList, self).remove(*items)
        self._needs_arrange = True

    def draw(self, surface):
        if self._needs_arrange:
            self.arrange_menu_items()
            self._needs_arrange = False
        super(VisualSpriteList, self).draw(surface)

    def arrange_menu_items(self):
        """ Iterate through menu items and position them in the menu
        Defaults to a multi-column layout with items placed horizontally first.

        :returns: None
        """
        if not len(self):
            return

        # max_width = 0
        max_height = 0
        for item in self.sprites():
            # max_width = max(max_width, item.rect.width)
            max_height = max(max_height, item.rect.height)

        self.update_rect_from_parent()
        width, height = self.rect.size

        items_per_column = math.ceil(len(self) / self.columns)

        if self.expand:
            # fill available space
            line_spacing = self.line_spacing
            if not line_spacing:
                line_spacing = height // items_per_column
        else:
            line_spacing = int(max_height * 1.2)

        column_spacing = width // self.columns

        # TODO: pagination API

        for index, item in enumerate(self.sprites()):
            oy, ox = divmod(index, self.columns)
            item.rect.topleft = ox * column_spacing, oy * line_spacing

    def determine_cursor_movement(self, *args):
        """ Given an event, determine a new selected item offset

        You must pass the currently selected object
        The return value will be the newly selected object index

        :param index: Index of the item in the list
        :param event: pygame.Event
        :returns: New menu item offset
        """
        if self.orientation == 'horizontal':
            return self.determine_cursor_movement_horizontal(*args)
        else:
            raise RuntimeError

    def determine_cursor_movement_horizontal(self, index, event):
        """ Given an event, determine a new selected item offset

        You must pass the currently selected object
        The return value will be the newly selected object index

        This is for menus that are laid out horizontally first:
           [1] [2] [3]
           [4] [5]

        :param index: Index of the item in the list
        :param event: pygame.Event
        :returns: New menu item offset
        """
        if not len(self):
            return 0

        if event.type == pygame.KEYDOWN:

            # ignore left/right if there is only one column
            if self.columns > 1:
                if event.key == pygame.K_LEFT:
                    index -= 1

                elif event.key == pygame.K_RIGHT:
                    index += 1

            if event.key == pygame.K_DOWN:
                index += self.columns

            elif event.key == pygame.K_UP:
                index -= self.columns

            # wrap the cursor position
            items = len(self)
            if index < 0:
                index = items - abs(index)
            if index >= items:
                index -= items

        return index
