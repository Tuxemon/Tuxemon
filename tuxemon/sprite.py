# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import math
from collections.abc import Callable, Container, Iterator, Sequence
from typing import (
    TYPE_CHECKING,
    Any,
    Final,
    Generic,
    Literal,
    Optional,
    TypeVar,
    Union,
    overload,
)

from pygame.rect import Rect
from pygame.sprite import DirtySprite, Group, LayeredUpdates
from pygame.sprite import Sprite as PySprite
from pygame.surface import Surface
from pygame.transform import rotozoom, scale

from tuxemon import graphics
from tuxemon.platform.const import buttons
from tuxemon.platform.events import PlayerInput
from tuxemon.surfanim import SurfaceAnimation
from tuxemon.tools import scale as tuxemon_scale

if TYPE_CHECKING:
    from tuxemon.db import BattleIconsModel
    from tuxemon.menu.interface import MenuItem
    from tuxemon.monster import Monster

logger = logging.getLogger()


dummy_image: Final = Surface((0, 0))


class Sprite(DirtySprite):
    _original_image: Optional[Surface]
    _image: Optional[Surface]
    _rect: Rect

    def __init__(
        self,
        *args: Group,
        image: Optional[Surface] = None,
        animation: Optional[SurfaceAnimation] = None,
    ) -> None:
        super().__init__(*args)
        self.visible: bool = True
        self._rotation: int = 0
        self._rect = Rect(0, 0, 0, 0)
        self.image = image
        self.animation = animation
        self._width: int = 0
        self._height: int = 0
        self._needs_rescale: bool = False
        self._needs_update: bool = False
        self.player: bool = False

    def update(self, time_delta: float = 0, *args: Any, **kwargs: Any) -> None:
        """
        Update the sprite.

        Parameters:
            time_delta: The time delta since the last update. Defaults to 0.
            args: Additional arguments.
            kwargs: Additional keyword arguments.
        """
        super().update(time_delta, *args, **kwargs)

        if self.animation is not None:
            self.animation.update(time_delta)

    def draw(
        self,
        surface: Surface,
        rect: Optional[Rect] = None,
    ) -> Rect:
        """
        Draw the sprite to the surface.

        This operation does not scale the sprite, so it may exceed
        the size of the area passed.

        Parameters:
            surface: The surface to draw on.
            rect: The area to contain the sprite. Defaults to None.

        Returns:
            The area of the surface that was modified.
        """
        # should draw to surface without generating a cached copy
        if rect is None:
            rect = surface.get_rect()
        return self._draw(surface, rect)

    def _draw(
        self,
        surface: Surface,
        rect: Rect,
    ) -> Rect:
        """
        Draw the sprite to the surface.

        Parameters:
            surface: The surface to draw on.
            rect: The area to contain the sprite.

        Returns:
            The area of the surface that was modified.
        """
        return surface.blit(self.image, rect)

    @property
    def rect(self) -> Rect:
        """
        Get the rectangle of the sprite.

        Returns:
            The rectangle of the sprite.
        """
        return self._rect

    @rect.setter
    def rect(self, rect: Optional[Rect]) -> None:
        """
        Set the rectangle of the sprite.

        Parameters:
            rect: The new rectangle of the sprite.
        """
        if rect is None:
            rect = Rect(0, 0, 0, 0)

        if rect != self._rect:
            self._rect = rect
            self._needs_update = True

    @property
    def image(self) -> Surface:
        """
        Get the image of the sprite.

        Returns:
            The image of the sprite.
        """
        # should always be a cached copy
        if self.animation is not None:
            return self.animation.get_current_frame()

        if self._needs_update:
            self.update_image()
            self._needs_update = False
            self._needs_rescale = False
        return self._image if self._image and self.visible else dummy_image

    @image.setter
    def image(self, image: Optional[Surface]) -> None:
        """
        Set the image of the sprite.

        Parameters:
            image: The new image of the sprite.
        """
        if image is not None:
            self.animation = None
            rect = image.get_rect()
            self.rect.size = rect.size

        self._original_image = image
        self._image = image
        self._needs_update = True

    @property
    def animation(self) -> Optional[SurfaceAnimation]:
        """
        Get the animation of the sprite.

        Returns:
            The animation of the sprite.
        """
        return self._animation

    @animation.setter
    def animation(self, animation: Optional[SurfaceAnimation]) -> None:
        """
        Set the animation of the sprite.

        Parameters:
            animation: The new animation of the sprite.
        """
        self._animation = animation
        if animation is not None:
            self.image = None
            self.rect.size = animation.get_rect().size

    def update_image(self) -> None:
        """
        Update the image of the sprite.
        """
        image: Optional[Surface]
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

    @property
    def width(self) -> int:
        """
        Get the width of the sprite.

        Returns:
            The width of the sprite.
        """
        return self._width

    @width.setter
    def width(self, width: int) -> None:
        """
        Set the width of the sprite.

        Parameters:
            width: The new width of the sprite.
        """
        width = int(round(width, 0))
        if not width == self._width:
            self._width = width
            self._needs_rescale = True
            self._needs_update = True

    @property
    def height(self) -> int:
        """
        Get the height of the sprite.

        Returns:
            The height of the sprite.
        """
        return self._height

    @height.setter
    def height(self, height: int) -> None:
        """
        Set the height of the sprite.

        Parameters:
            height: The new height of the sprite.
        """
        height = int(round(height, 0))
        if not height == self._height:
            self._height = height
            self._needs_rescale = True
            self._needs_update = True

    @property
    def rotation(self) -> int:
        """
        Get the rotation of the sprite.

        Returns:
            The rotation of the sprite.
        """
        return self._rotation

    @rotation.setter
    def rotation(self, value: float) -> None:
        """
        Set the rotation of the sprite.

        Parameters:
            value: The new rotation of the sprite.
        """
        value = int(round(value, 0)) % 360
        if not value == self._rotation:
            self._rotation = value
            self._needs_update = True

    def get_size(self) -> tuple[int, int]:
        """
        Get the size of the sprite.

        Returns:
            The size of the sprite.
        """
        return self._width, self._height

    def set_position(self, x: int, y: int) -> None:
        """
        Set the position of the sprite.

        Parameters:
            x: The new x-coordinate of the sprite.
            y: The new y-coordinate of the sprite.
        """
        self.rect.x = x
        self.rect.y = y

    def get_position(self) -> tuple[int, int]:
        """
        Get the position of the sprite.

        Returns:
            The position of the sprite.
        """
        return self.rect.x, self.rect.y

    def is_visible(self) -> bool:
        """
        Check if the sprite is visible.

        Returns:
            Whether the sprite is visible.
        """
        return self.visible

    def toggle_visible(sprite: Sprite) -> None:
        """
        Toggles the visibility of a sprite.

        Parameters:
            sprite: The sprite to toggle visibility for.
        """
        sprite.visible = not sprite.visible


class CaptureDeviceSprite(Sprite):
    def __init__(
        self,
        *,
        tray: Sprite,
        monster: Optional[Monster],
        sprite: Sprite,
        state: str,
        icon: BattleIconsModel,
    ) -> None:
        self.tray = tray
        self.monster = monster
        self.sprite = sprite
        self.state = state
        self.empty_img = graphics.load_and_scale(icon.icon_empty)
        self.faint_img = graphics.load_and_scale(icon.icon_faint)
        self.alive_img = graphics.load_and_scale(icon.icon_alive)
        self.effected_img = graphics.load_and_scale(icon.icon_status)
        super().__init__()

    def update_state(self) -> str:
        """
        Updates the state of the capture device.

        Returns:
            The new state.

        """
        if self.state == "empty":
            self.sprite.image = self.empty_img
            return "empty"

        assert self.monster

        if any(t.slug == "faint" for t in self.monster.status):
            self.state = "faint"
            self.sprite.image = self.faint_img
        elif self.monster.status:
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


class SpriteGroup(LayeredUpdates, Generic[_GroupElement]):
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

    def add(self, *sprites: Union[PySprite, Any], **kwargs: Any) -> None:
        return LayeredUpdates.add(self, *sprites, **kwargs)

    def __iter__(self) -> Iterator[_GroupElement]:
        return LayeredUpdates.__iter__(self)

    def sprites(self) -> Sequence[_GroupElement]:
        # Pygame typing is awful. Ignore Mypy here.
        return LayeredUpdates.sprites(self)

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

    def calc_bounding_rect(self) -> Rect:
        """A rect object that contains all sprites of this group."""
        sprites = self.sprites()
        if len(sprites) == 1:
            return Rect(sprites[0].rect)
        else:
            return sprites[0].rect.unionall([s.rect for s in sprites[1:]])

    def swap(
        self, original_sprite: _GroupElement, new_sprite: _GroupElement
    ) -> None:
        """
        Swap the positions of two sprites in the group.
        """
        self.remove(original_sprite)
        self.add(new_sprite)


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
            New menu item offset.

        """
        # TODO: some sort of smart way to pick items based on location on
        # screen
        if not len(self):
            return 0

        if event.pressed and event.button in self._allowed_input():
            seeking_index = True
            while seeking_index:
                index = self._advance_input(index, event.button)

                seeking_index = not self.sprites()[index].enabled

        return index


class RelativeGroup(MenuSpriteGroup[_MenuElement]):
    """
    Drawing operations are relative to the group's rect.
    """

    rect = Rect(0, 0, 0, 0)

    def __init__(
        self,
        *,
        parent: Union[RelativeGroup[Any], Callable[[], Rect]],
        **kwargs: Any,
    ) -> None:
        self.parent = parent
        super().__init__(**kwargs)

    def calc_absolute_rect(
        self,
        rect: Rect,
    ) -> Rect:
        self.update_rect_from_parent()
        return rect.move(self.rect.topleft)

    def update_rect_from_parent(self) -> None:
        if callable(self.parent):
            self.rect = self.parent()
        else:
            self.rect = Rect(self.parent.rect)

    def draw(
        self,
        surface: Surface,
    ) -> list[Rect]:
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

    # default, and only implemented
    orientation: Literal["horizontal"] = "horizontal"
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
        self.max_width_per_column: Optional[int] = None

    @property
    def columns(self) -> int:
        return self._columns

    @columns.setter
    def columns(self, value: int) -> None:
        self._columns = value
        self._needs_arrange = True

    def calc_bounding_rect(self) -> Rect:
        if self._needs_arrange:
            self.arrange_menu_items()
        return super().calc_bounding_rect()

    def add(self, *sprites: Union[PySprite, Any], **kwargs: Any) -> None:
        """
        Add something to the stacker.

        Do not add iterables to this function. Use 'extend'.

        Parameters:
            item: Stuff to add.
        """
        super().add(*sprites, **kwargs)
        self._needs_arrange = True

    def remove(self, *items: Union[PySprite, Any]) -> None:
        super().remove(*items)
        self._needs_arrange = True

    def clear(
        self, surface: Any = None, bgsurf: Any = None, special_flags: int = 0
    ) -> None:
        for i in self.sprites():
            super().remove(i)
        self._needs_arrange = True

    def draw(self, surface: Surface) -> list[Rect]:
        if self._needs_arrange:
            self.arrange_menu_items()
        dirty = super().draw(surface)
        return dirty

    def arrange_menu_items(self) -> None:
        """
        Iterate through menu items and position them in the menu.
        Defaults to a multi-column layout with items placed horizontally first.

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

        if self.max_width_per_column is not None:
            self._columns = max(1, width // max(1, self.max_width_per_column))

        items_per_column = math.ceil(len(self) / self._columns)

        if self.expand:
            logger.debug("expanding menu...")
            # fill available space
            line_spacing = self.line_spacing or (height // items_per_column)
        else:
            line_spacing = int(max_height * 1.2)

        column_spacing = width // self._columns

        # TODO: pagination API

        for index, item in enumerate(self.sprites()):
            oy, ox = divmod(index, self._columns)
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
