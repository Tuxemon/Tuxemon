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

from __future__ import annotations
import logging
import math

import pygame
from pygame.transform import rotozoom
from pygame.transform import scale

from pygame.rect import Rect
from tuxemon.platform.const import buttons
from tuxemon.surfanim import SurfaceAnimation
from tuxemon import graphics
from tuxemon.tools import scale as set
from typing import Optional, Callable, Any, Sequence, List, Union, TYPE_CHECKING,\
    TypeVar, Generic, Iterator, overload, Final
from tuxemon.platform.events import PlayerInput

if TYPE_CHECKING:
    from tuxemon.monster import Monster

logger = logging.getLogger()


dummy_image: Final = pygame.surface.Surface((0, 0))


class Sprite(pygame.sprite.DirtySprite):
    _original_image: pygame.surface.Surface
    _image: pygame.surface.Surface
    _rect: pygame.rect.Rect
    image: pygame.surface.Surface
    rect: pygame.rect.Rect

    def __init__(
        self,
        *args: pygame.sprite.Group,
        image: Optional[pygame.surface.Surface] = None,
    ) -> None:
        super().__init__(*args)
        self.visible = True
        self._rotation = 0
        self._rect = dummy_image.get_rect()
        self.image = image
        self._width = 0
        self._height = 0
        self._needs_rescale = False
        self._needs_update = False

    def update(self, time_delta: float = 0, *args: Any, **kwargs: Any) -> None:

        super().update(time_delta, *args, **kwargs)

        if isinstance(self.image, SurfaceAnimation):
            self.image.update(time_delta)

    def draw(
        self,
        surface: pygame.surface.Surface,
        rect: Optional[pygame.rect.Rect] = None,
    ) -> pygame.rect.Rect:
        """
        Draw the sprite to the surface.

        This operation does not scale the sprite, so it may exceed
        the size of the area passed.

        Parameters:
            surface: Surface to be drawn on.
            rect: Area to contain the sprite.

        Returns:
            Area of the surface that was modified.

        """
        # should draw to surface without generating a cached copy
        if rect is None:
            rect = surface.get_rect()
        return self._draw(surface, rect)

    def _draw(
        self,
        surface: pygame.surface.Surface,
        rect: pygame.rect.Rect,
    ) -> pygame.rect.Rect:
        return surface.blit(self._image, rect)

    @property
    def rect(self) -> Rect:
        return self._rect

    @rect.setter
    def rect(self, rect: Rect) -> None:
        if not rect == self._rect:
            self._rect = rect
            self._needs_update = True

    @property
    def image(self) -> pygame.surface.Surface:
        # should always be a cached copy
        if self._needs_update:
            self.update_image()
            self._needs_update = False
            self._needs_rescale = False
        return self._image

    @image.setter
    def image(self, image: Optional[pygame.surface.Surface]) -> None:
        if image is None:
            image = dummy_image

        rect = image.get_rect()
        self.rect.size = rect.size
        self._original_image = image
        self._image = image
        self._needs_update = True

    def update_image(self) -> None:
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
    def width(self) -> int:
        return self._width

    @width.setter
    def width(self, width: int) -> None:
        width = int(round(width, 0))
        if not width == self._width:
            self._width = width
            self._needs_rescale = True
            self._needs_update = True

    # width and height are API that may not stay
    @property
    def height(self) -> int:
        return self._height

    @height.setter
    def height(self, height: int) -> None:
        height = int(round(height, 0))
        if not height == self._height:
            self._height = height
            self._needs_rescale = True
            self._needs_update = True

    @property
    def rotation(self) -> int:
        return self._rotation

    @rotation.setter
    def rotation(self, value: float) -> None:
        value = int(round(value, 0)) % 360
        if not value == self._rotation:
            self._rotation = value
            self._needs_update = True


class CaptureDeviceSprite(Sprite):
    def __init__(
        self,
        *,
        tray: Sprite,
        monster: Optional[Monster],
        sprite: Sprite,
        state: str,
    ) -> None:
        self.tray = tray
        self.monster = monster
        self.sprite = sprite
        self.state = state
        self.empty = graphics.load_and_scale("gfx/ui/combat/empty_slot_icon.png")
        self.faint = graphics.load_and_scale("gfx/ui/icons/party/party_icon03.png")
        self.alive = graphics.load_and_scale("gfx/ui/icons/party/party_icon01.png")
        self.effected = graphics.load_and_scale("gfx/ui/icons/party/party_icon02.png")
        super().__init__()

    def update_state(self) -> str:
        """
        Updates the state of the capture device.

        Returns:
            The new state.

        """
        if self.state == "empty":
            self.sprite.image = self.empty
        else:
            assert self.monster
            if any(t for t in self.monster.status if t.slug == "status_faint"):
                self.state = "faint"
                self.sprite.image = self.faint
            elif len(self.monster.status) > 0:
                self.state = "effected"
                self.sprite.image = self.effected
            else:
                self.state = "alive"
                self.sprite.image = self.alive
        return self.state

    def draw(
        self,
        animate: Callable[..., object],
    ) -> None:
        """
        Animates the capture device in game.

        Parameters:
            animate: The animation function.

        """
        sprite = self.sprite
        sprite.image = graphics.convert_alpha_to_colorkey(sprite.image)
        sprite.image.set_alpha(0)
        animate(sprite.image, set_alpha=255, initial=0)
        animate(sprite.rect, bottom=self.tray.rect.top + set(3))


_GroupElement = TypeVar("_GroupElement", bound=pygame.sprite.Sprite)


class SpriteGroup(pygame.sprite.LayeredUpdates, Generic[_GroupElement]):
    """
    Sane variation of a pygame sprite group.

    Features:
    * Supports Layers
    * Supports Index / Slice
    * Supports skipping sprites without an image
    * Supports sprites with visible flag
    * Get bounding rect of all children

    """

    def __init__(self, *, default_layer: int = 0) -> None:
        super().__init__(default_layer=default_layer)

    def add(self, *sprites: pygame.sprite.Sprite, **kwargs: Any) -> None:
        return pygame.sprite.LayeredUpdates.add(self, *sprites, **kwargs)

    def __iter__(self) -> Iterator[_GroupElement]:
        return pygame.sprite.LayeredUpdates.__iter__(self)

    def sprites(self) -> Sequence[_GroupElement]:
        # Pygame typing is awful. Ignore Mypy here.
        return pygame.sprite.LayeredUpdates.sprites(self)

    def __nonzero__(self) -> bool:
        return bool(self.sprites())

    @overload
    def __getitem__(
        self,
        item: int,
    ) -> _GroupElement:
        pass

    @overload
    def __getitem__(
        self,
        item: slice,
    ) -> Sequence[_GroupElement]:
        pass

    def __getitem__(
        self,
        item: Union[int, slice],
    ) -> Union[_GroupElement, Sequence[_GroupElement]]:
        # patch in indexing / slicing support
        return self.sprites()[item]

    def draw(
        self,
        surface: pygame.surface.Surface,
    ) -> List[pygame.rect.Rect]:
        spritedict = self.spritedict
        surface_blit = surface.blit
        dirty = self.lostsprites
        self.lostsprites = []
        dirty_append = dirty.append

        for s in self.sprites():
            if getattr(s, "image", None) is None:
                continue

            if not getattr(s, "visible", True):
                continue

            if isinstance(s.image, SurfaceAnimation):
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

    def calc_bounding_rect(self) -> pygame.rect.Rect:
        """A rect object that contains all sprites of this group"""
        sprites = self.sprites()
        if not sprites:
            return self.rect
        elif len(sprites) == 1:
            return pygame.rect.Rect(sprites[0].rect)
        else:
            return sprites[0].rect.unionall([s.rect for s in sprites[1:]])


class RelativeGroup(SpriteGroup[_GroupElement]):
    """
    Drawing operations are relative to the group's rect.
    """

    rect = pygame.rect.Rect(0, 0, 0, 0)

    def __init__(
        self,
        *,
        parent: Union[RelativeGroup[Any], Callable[[], pygame.rect.Rect],  None] = None,
        **kwargs: Any,
    ) -> None:
        self.parent = parent
        super().__init__(**kwargs)

    def calc_absolute_rect(
        self,
        rect: pygame.rect.Rect,
    ) -> pygame.rect.Rect:
        self.update_rect_from_parent()
        return rect.move(self.rect.topleft)

    def update_rect_from_parent(self) -> None:
        try:
            self.rect = self.parent()
        except TypeError:
            self.rect = pygame.rect.Rect(self.parent.rect)

    def draw(
        self,
        surface: pygame.surface.Surface,
    ) -> List[pygame.rect.Rect]:
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

            if not getattr(s, "visible", True):
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


class MenuSpriteGroup(SpriteGroup[_GroupElement]):
    """
    Sprite Group to be used for menus.

    Includes functions for moving a cursor around the screen.

    """

    def determine_cursor_movement(self, index: int, event: PlayerInput) -> int:
        """
        Given an event, determine a new selected item offset.

        You must pass the currently selected object.
        The return value will be the newly selected object index.

        Parameters:
            index: Index of the item in the list.
            event: Player event that may cause to select another menu item.

        Returns:
            New menu item offset

        """
        # TODO: some sort of smart way to pick items based on location on screen
        if not len(self):
            return 0

        if event.pressed:
            # ignore left/right if there is only one column
            if event.button == buttons.LEFT:
                index -= 1

            elif event.button == buttons.RIGHT:
                index += 1

            if event.button == buttons.DOWN:
                index += 1

            elif event.button == buttons.UP:
                index -= 1

            # wrap the cursor position
            items = len(self)
            if index < 0:
                index = items - abs(index)
            if index >= items:
                index -= items

        return index


class VisualSpriteList(RelativeGroup[_GroupElement]):
    """
    Sprite group which can be configured to arrange the children
    sprites into columns.
    """

    orientation = "horizontal"  # default, and only implemented
    expand = True  # will fill all space of parent, if false, will be more compact

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._needs_arrange = False
        self._columns = 1
        self.line_spacing: Optional[int] = None

    @property
    def columns(self) -> int:
        return self._columns

    @columns.setter
    def columns(self, value: int) -> None:
        self._columns = value
        self._needs_arrange = True

    def calc_bounding_rect(self) -> pygame.rect.Rect:
        if self._needs_arrange:
            self.arrange_menu_items()
        return super().calc_bounding_rect()

    def add(
        self,
        *sprites: pygame.sprite.Sprite,
        **kwargs: Any,
    ) -> None:
        """
        Add something to the stacker.

        Do not add iterables to this function. Use 'extend'.

        Parameters:
            item: Stuff to add.

        """
        super().add(*sprites, **kwargs)
        self._needs_arrange = True

    def remove(
        self,
        *items: pygame.sprite.Sprite,
    ) -> None:
        super().remove(*items)
        self._needs_arrange = True

    def draw(
        self,
        surface: pygame.surface.Surface,
    ) -> None:
        if self._needs_arrange:
            self.arrange_menu_items()
        super().draw(surface)

    def arrange_menu_items(self) -> None:
        """Iterate through menu items and position them in the menu
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
            logger.debug("expanding menu...")
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

        self._needs_arrange = False

    def determine_cursor_movement(
        self,
        index: int,
        event: PlayerInput,
    ) -> int:
        """
        Given an event, determine a new selected item offset.

        You must pass the currently selected object.
        The return value will be the newly selected object index.

        Parameters:
            index: Index of the item in the list.
            event: Player event that may cause to select another menu item.

        Returns:
            New menu item offset

        """
        if self.orientation == "horizontal":
            return self._determine_cursor_movement_horizontal(index, event)
        else:
            raise RuntimeError

    def _determine_cursor_movement_horizontal(
        self,
        index: int,
        event: PlayerInput,
    ) -> int:
        """Given an event, determine a new selected item offset

        You must pass the currently selected object.
        The return value will be the newly selected object index.

        This is for menus that are laid out horizontally first:
           [1] [2] [3]
           [4] [5]

        Works pretty well for most menus, but large grids may require
        handling them differently.

        Parameters:
            index: Index of the item in the list.
            event: Player event that may cause to select another menu item.

        Returns:
            New menu item offset

        """
        # sanity check:
        # if there are 0 or 1 enabled items, then ignore movement
        enabled = len([i for i in self if i.enabled])
        if enabled < 2:
            return index

        if event.pressed:

            # in order to accommodate disabled menu items,
            # the mod incrementer will loop until a suitable
            # index is found...one that is not disabled.
            items = len(self)
            mod = 0

            # horizontal movement: left and right will inc/dec mod by one
            if self.columns > 1:
                if event.button == buttons.LEFT:
                    mod -= 1

                elif event.button == buttons.RIGHT:
                    mod += 1

            # vertical movement: up/down will inc/dec the mod by adjusted
            # value of number of items in a column
            rows, remainder = divmod(items, self.columns)
            row, col = divmod(index, self.columns)

            # down key pressed
            if event.button == buttons.DOWN:
                if remainder:
                    if row == rows:
                        mod += remainder

                    elif col < remainder:
                        mod += self.columns
                    else:
                        if row == rows - 1:
                            mod += self.columns + remainder
                        else:
                            mod += self.columns

                else:
                    mod = self.columns

            # up key pressed
            elif event.button == buttons.UP:
                if remainder:
                    if row == 0:
                        if col < remainder:
                            mod -= remainder
                        else:
                            mod += self.columns * (rows - 1)
                    else:
                        mod -= self.columns

                else:
                    mod -= self.columns

            original_index = index
            seeking_index = True
            # seeking_index once false, will exit the loop
            while seeking_index and mod:
                index += mod

                # wrap the cursor position
                if index < 0:
                    index = items - abs(index)
                if index >= items:
                    index -= items

                # while looking for a suitable index, we've looked over all choices
                # just raise an error for now, instead of infinite looping
                # TODO: some graceful way to handle situations where cannot find an index
                if index == original_index:
                    raise RuntimeError

                seeking_index = not self._spritelist[index].enabled

        return index
