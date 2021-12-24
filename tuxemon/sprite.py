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
from tuxemon.tools import scale as tuxemon_scale
from typing import Optional, Callable, Any, Sequence, List, Union, TYPE_CHECKING,\
    TypeVar, Generic, Iterator, overload, Final, Tuple, Literal, Container
from tuxemon.platform.events import PlayerInput

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.menu.interface import MenuItem

logger = logging.getLogger()


dummy_image: Final = pygame.surface.Surface((0, 0))


class Sprite(pygame.sprite.DirtySprite):
    _original_image: Optional[pygame.surface.Surface]
    _image: Optional[pygame.surface.Surface]
    _rect: pygame.rect.Rect

    def __init__(
        self,
        *args: pygame.sprite.Group,
        image: Optional[pygame.surface.Surface] = None,
        animation: Optional[SurfaceAnimation] = None,
    ) -> None:
        super().__init__(*args)
        self.visible = True
        self._rotation = 0
        self._rect = Rect(0, 0, 0, 0)
        self.image = image
        self.animation = animation
        self._width = 0
        self._height = 0
        self._needs_rescale = False
        self._needs_update = False

    def update(self, time_delta: float = 0, *args: Any, **kwargs: Any) -> None:

        super().update(time_delta, *args, **kwargs)

        if self.animation is not None:
            self.animation.update(time_delta)

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
        return surface.blit(self.image, rect)

    @property
    def rect(self) -> Rect:
        return self._rect

    @rect.setter
    def rect(self, rect: Optional[Rect]) -> None:
        if rect is None:
            rect = Rect(0, 0, 0, 0)

        if rect != self._rect:
            self._rect = rect
            self._needs_update = True

    @property
    def image(self) -> pygame.surface.Surface:
        # should always be a cached copy
        if self.animation is not None:
            return self.animation.get_current_frame()

        if self._needs_update:
            self.update_image()
            self._needs_update = False
            self._needs_rescale = False
        return self._image if self._image and self.visible else dummy_image

    @image.setter
    def image(self, image: Optional[pygame.surface.Surface]) -> None:
        if image is not None:
            self.animation = None
            rect = image.get_rect()
            self.rect.size = rect.size

        self._original_image = image
        self._image = image
        self._needs_update = True

    @property
    def animation(self) -> Optional[SurfaceAnimation]:
        return self._animation

    @animation.setter
    def animation(self, animation: Optional[SurfaceAnimation]) -> None:

        self._animation = animation
        if animation is not None:
            self.image = None
            self.rect.size = animation.get_rect().size

    def update_image(self) -> None:

        image: Optional[pygame.surface.Surface]
        if self._original_image is not None and self._needs_rescale:
            w = self.rect.width if self._width is None else self._width
            h = self.rect.height if self._height is None else self._height
            image = scale(self._original_image, (w, h))
            center = self.rect.center
            self.rect.size = w, h
            self.rect.center = center
        else:
            image = self._original_image

        if image is not None and self._rotation:
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
        self.empty_img = graphics.load_and_scale(
            "gfx/ui/combat/empty_slot_icon.png",
        )
        self.faint_img = graphics.load_and_scale(
            "gfx/ui/icons/party/party_icon03.png",
        )
        self.alive_img = graphics.load_and_scale(
            "gfx/ui/icons/party/party_icon01.png",
        )
        self.effected_img = graphics.load_and_scale(
            "gfx/ui/icons/party/party_icon02.png",
        )
        super().__init__()

    def update_state(self) -> str:
        """
        Updates the state of the capture device.

        Returns:
            The new state.

        """
        if self.state == "empty":
            self.sprite.image = self.empty_img
        else:
            assert self.monster
            if any(t for t in self.monster.status if t.slug == "status_faint"):
                self.state = "faint"
                self.sprite.image = self.faint_img
            elif len(self.monster.status) > 0:
                self.state = "effected"
                self.sprite.image = self.effected_img
            else:
                self.state = "alive"
                self.sprite.image = self.alive_img
        return self.state

    def animate_capture(
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
        animate(sprite.rect, bottom=self.tray.rect.top + tuxemon_scale(3))


_GroupElement = TypeVar("_GroupElement", bound=Sprite)


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

    def __bool__(self) -> bool:
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

    def calc_bounding_rect(self) -> pygame.rect.Rect:
        """A rect object that contains all sprites of this group"""
        sprites = self.sprites()
        if len(sprites) == 1:
            return pygame.rect.Rect(sprites[0].rect)
        else:
            return sprites[0].rect.unionall([s.rect for s in sprites[1:]])


_MenuElement = TypeVar("_MenuElement", bound="MenuItem[Any]")


class MenuSpriteGroup(SpriteGroup[_MenuElement]):
    """
    Sprite Group to be used for menus.

    Includes functions for moving a cursor around the screen.

    """

    _simple_movement_dict: Final = {
        buttons.LEFT: -1,
        buttons.RIGHT: 1,
        buttons.UP: -1,
        buttons.DOWN: 1,
    }
    expand = False  # Used in subclasses only

    def arrange_menu_items(self) -> None:
        """Iterate through menu items and position them in the menu."""
        pass

    def _allowed_input(self) -> Container[int]:
        """Returns allowed buttons."""
        return set(self._simple_movement_dict)

    def _advance_input(self, index: int, button: int) -> int:
        """Advance the index given the input."""
        return (index + self._simple_movement_dict[button]) % len(self)

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
        # TODO: some sort of smart way to pick items based on location on
        # screen
        if not len(self):
            return 0

        if event.pressed and event.button in self._allowed_input():

            original_index = index

            seeking_index = True
            while seeking_index:
                index = self._advance_input(index, event.button)

                if index == original_index:
                    raise RuntimeError

                seeking_index = not self.sprites()[index].enabled

        return index


class RelativeGroup(MenuSpriteGroup[_MenuElement]):
    """
    Drawing operations are relative to the group's rect.
    """

    rect = pygame.rect.Rect(0, 0, 0, 0)

    def __init__(
        self,
        *,
        parent: Union[RelativeGroup[Any], Callable[[], pygame.rect.Rect]],
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
        if callable(self.parent):
            self.rect = self.parent()
        else:
            self.rect = pygame.rect.Rect(self.parent.rect)

    def draw(
        self,
        surface: pygame.surface.Surface,
    ) -> List[pygame.rect.Rect]:
        self.update_rect_from_parent()
        topleft = self.rect.topleft

        # The identity of the rectangle should be kept, as animations may
        # keep a reference to it
        for s in self.sprites():
            s.rect.move_ip(topleft)

        try:
            dirty = super().draw(surface)
        finally:
            for s in self.sprites():
                s.rect.move_ip((-topleft[0], -topleft[1]))
        return dirty


class VisualSpriteList(RelativeGroup[_MenuElement]):
    """
    Sprite group which can be configured to arrange the children
    sprites into columns.
    """

    orientation: Literal["horizontal"] = "horizontal"  # default, and only implemented
    expand = True  # True: fill all space of parent. False: more compact
    _2d_movement_dict: Final = {
        buttons.LEFT: ("lr", -1),
        buttons.RIGHT: ("lr", 1),
        buttons.UP: ("tb", -1),
        buttons.DOWN: ("tb", 1),
    }

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

    def clear(self) -> None:
        for i in self.sprites():
            super().remove(i)
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

    def _lr_to_tb_index(
        self,
        lr_index: int,
        orientation: Literal["horizontal"],
    ) -> int:
        """Convert left/right index to top/bottom index."""
        if orientation == "horizontal":
            rows, remainder = divmod(len(self), self.columns)
            row, col = divmod(lr_index, self.columns)

            n_complete_columns = col if col < remainder else remainder
            n_incomplete_columns = 0 if col < remainder else col - remainder
            return (
                n_complete_columns * (rows + 1)
                + n_incomplete_columns * rows
                + row
            )
        else:
            raise NotImplementedError

    def _tb_to_lr_index(
        self,
        tb_index: int,
        orientation: Literal["horizontal"],
    ) -> int:
        """Convert top/bottom index to left/right index."""
        if orientation == "horizontal":
            rows, remainder = divmod(len(self), self.columns)

            if tb_index < remainder * (rows + 1):
                col, row = divmod(tb_index, rows + 1)
            else:
                col, row = divmod(tb_index - remainder * (rows + 1), rows)
                col += remainder

            return row * self.columns + col
        else:
            raise NotImplementedError

    def _allowed_input(self) -> Container[int]:
        return set(self._2d_movement_dict)

    def _advance_input(self, index: int, button: int) -> int:
        """Advance the index given the input."""

        # Layout (horizontal):
        #        0 1 2 3 4 ... columns-1
        #      0 X X X X X ... X
        #      1 X X X X X ... X
        #      2 X X X X X ... X
        #    ... . . . . . ... .
        # rows-1 X X X X X ... X
        #   rows X X _ _ _ ... _
        #          ^
        #          |
        #       remainder=2

        index_type, incr = self._2d_movement_dict[button]

        if index_type == "tb":
            index = self._lr_to_tb_index(index, self.orientation)

        index += incr
        index %= len(self)

        if index_type == "tb":
            index = self._tb_to_lr_index(index, self.orientation)

        return index
