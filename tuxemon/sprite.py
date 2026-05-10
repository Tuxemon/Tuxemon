# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Callable, Container, Iterator, Sequence
from math import ceil
from typing import (
    TYPE_CHECKING,
    Any,
    Final,
    Generic,
    Literal,
    TypeVar,
    overload,
)

from pygame import SRCALPHA
from pygame.rect import FRect, Rect
from pygame.sprite import DirtySprite, LayeredUpdates
from pygame.sprite import Sprite as PySprite
from pygame.surface import Surface
from pygame.transform import rotate, rotozoom, scale

from tuxemon.menu.grid_index_model import GridIndexModel
from tuxemon.platform.const import buttons
from tuxemon.platform.events import PlayerInput
from tuxemon.surfanim import SurfaceAnimation

if TYPE_CHECKING:
    from tuxemon.db import BattleIconsModel
    from tuxemon.entity.party import PartyHandler
    from tuxemon.menu.interface import MenuItem
    from tuxemon.monster.monster import Monster
    from tuxemon.prepare import DisplayContext

logger = logging.getLogger()


class Sprite(DirtySprite):
    _dummy_image: Surface = Surface((0, 0))
    _original_image: Surface | None
    _image: Surface | None
    _rect: Rect

    def __init__(
        self,
        *args: Any,
        image: Surface | None = None,
        animation: SurfaceAnimation | None = None,
    ) -> None:
        super().__init__(*args)
        self.visible: bool = True
        self._rotation: int = 0
        self._rect = Rect(0, 0, 0, 0)
        self._animation: SurfaceAnimation | None = None
        self._width: int = 0
        self._height: int = 0
        self._needs_rescale: bool = False
        self._needs_update: bool = False

        self.image = image
        if animation is not None:
            self.animation = animation

        self.player: bool = False
        self.base_image: Surface | None = None

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

    def draw(self, surface: Surface, rect: Rect | None = None) -> Rect:
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
    def rect(self, rect: FRect | Rect | None) -> None:
        """
        Set the rectangle of the sprite.

        Parameters:
            rect: The new rectangle of the sprite.
        """
        if rect is None:
            rect = Rect(0, 0, 0, 0)

        if rect != self._rect:
            if isinstance(rect, FRect):
                rect = Rect(rect.x, rect.y, rect.width, rect.height)
            self._rect = rect
            self._needs_update = True

    @property
    def image(self) -> Surface:
        if not self.visible:
            return Sprite._dummy_image

        if self.animation is not None:
            frame = self.animation.get_current_frame()

            if not (self._width or self._height or self._rotation):
                return frame

            if (
                self._needs_update
                or self._needs_rescale
                or self._image is None
            ):
                self.update_image(source=frame)
                self._needs_update = False

            return self._image or Sprite._dummy_image

        if self._needs_update:
            self.update_image()
            self._needs_update = False

        return self._image if self._image else Sprite._dummy_image

    @image.setter
    def image(self, image: Surface | None) -> None:
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
    def animation(self) -> SurfaceAnimation | None:
        """
        Get the animation of the sprite.

        Returns:
            The animation of the sprite.
        """
        return self._animation

    @animation.setter
    def animation(self, animation: SurfaceAnimation | None) -> None:
        self._animation = animation
        if animation is not None:
            self._image = None
            self._needs_update = True

            self._width = 0
            self._height = 0
            self._needs_rescale = False

            self.rect.size = animation.get_rect().size
        else:
            self._needs_update = True

    def update_image(self, source: Surface | None = None) -> None:
        base = source if source is not None else self._original_image
        if base is None:
            self._image = None
            return

        if self._width or self._height:
            w = self._width or base.get_width()
            h = self._height or base.get_height()
        else:
            w, h = base.get_size()

        if (w, h) != base.get_size():
            image = scale(base, (w, h))
        else:
            image = base

        center = self.rect.center
        self.rect.size = (w, h)
        self.rect.center = center

        if self._rotation:
            if self._rotation % 90 == 0:
                image = rotate(image, self._rotation)
            else:
                image = rotozoom(image, self._rotation, 1)
            rect = image.get_rect(center=self.rect.center)
            self.rect.size = rect.size
            self.rect.center = rect.center

        self._image = image
        self._width, self._height = w, h
        self._needs_rescale = False

    def reset_to_base_image(self) -> None:
        """
        Resets the sprite's image to its base image.
        """
        if self.base_image:
            self._rotation = 0
            self._width = 0
            self._height = 0
            self._needs_rescale = False
            self._needs_update = True
            self.image = self.base_image.copy()
        else:
            logger.warning("base_image is not set. Cannot reset.")

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
        width = round(width)
        self._width = width
        center = self.rect.center
        self.rect.width = width
        self.rect.center = center
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
        height = round(height)
        self._height = height
        center = self.rect.center
        self.rect.height = height
        self.rect.center = center
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
        value = round(value) % 360
        if value != self._rotation:
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
        self.rect.topleft = (x, y)

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

    def toggle_visible(self) -> None:
        """Toggles the visibility of a sprite."""
        self.visible = not self.visible


class HordeSprite(Sprite):
    """
    A minimalist HUD sprite for Horde Battles that displays the number
    of remaining monsters without using a background icon.
    """

    def __init__(
        self,
        opponent_party: PartyHandler,
        tray_rect: Rect,
        shadow_text_func: Callable[[str], Surface],
        context: DisplayContext,
    ) -> None:
        super().__init__()
        self.opponent_party = opponent_party
        self.tray_rect = tray_rect
        self.shadow_text = shadow_text_func
        self.context = context
        self.update_count_display()

    def update_count_display(self) -> bool:
        """Updates the sprite to show the current horde count as text only."""
        if self.is_defeated():
            return False
        horde_size = len(self.opponent_party.alive)
        horde_text = f"x{horde_size}"
        text_surface = self.shadow_text(horde_text)
        x_pad = self.context.scaling.scale_int(2)
        y_pad = self.context.scaling.scale_int(4)
        width = text_surface.get_width() + x_pad * 2
        height = text_surface.get_height() + y_pad * 2
        self.image = Surface((width, height), SRCALPHA)
        self.image.fill((0, 0, 0, 0))
        self.image.blit(text_surface, (x_pad, y_pad))
        self.rect = self.image.get_rect(bottom=self.tray_rect.bottom, right=0)
        return True

    def is_defeated(self) -> bool:
        """Checks if the entire horde is defeated."""
        return self.opponent_party.is_fainted

    def animate_in(self, animate_func: Callable[..., object]) -> None:
        """Animates the horde icon sliding into its final position."""
        animate_func(self.rect, right=self.tray_rect.right)


class CaptureDeviceSprite(Sprite):
    def __init__(
        self,
        *,
        tray: Sprite,
        monster: Monster | None,
        sprite: Sprite,
        icon: BattleIconsModel,
        context: DisplayContext,
    ) -> None:
        super().__init__()
        self.tray = tray
        self.monster = monster
        self.sprite = sprite
        self.icon = icon
        self.context = context
        self.state = self.resolve_status()
        self.update_image()

    def resolve_status(self) -> str:
        if self.monster is None:
            return "empty"
        if self.monster.is_fainted:
            return "faint"
        if self.monster.status.status_exists():
            return "effected"
        return "alive"

    def update_image(self, source: Surface | None = None) -> None:
        from tuxemon import graphics

        mapping = {
            "empty": graphics.load_and_scale(self.icon.icon_empty),
            "faint": graphics.load_and_scale(self.icon.icon_faint),
            "effected": graphics.load_and_scale(self.icon.icon_status),
            "alive": graphics.load_and_scale(self.icon.icon_alive),
        }
        self.sprite.image = mapping[self.state]

    def update_state(self) -> str:
        """Check for state changes and update the image if needed."""
        new_state = self.resolve_status()
        if new_state != self.state:
            self.state = new_state
            self.update_image()
        return self.state

    def animate_capture(self, animate: Callable[..., object]) -> None:
        """Fade in + slide up animation for the sprite."""
        from tuxemon import graphics

        sprite = self.sprite
        sprite.image = graphics.convert_alpha_to_colorkey(sprite.image)
        sprite.image.set_alpha(0)
        animate(sprite.image, set_alpha=255, initial=0)
        animate(
            sprite.rect,
            bottom=self.tray.rect.top + self.context.scaling.scale_int(3),
        )


_GroupElement = TypeVar("_GroupElement", bound=Sprite)


class SpriteGroup(
    LayeredUpdates,  # type: ignore[type-arg]
    Generic[_GroupElement],
):
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

    def add(self, *sprites: PySprite | Any, **kwargs: Any) -> None:
        return LayeredUpdates.add(self, *sprites, **kwargs)

    def __iter__(self) -> Iterator[_GroupElement]:
        return LayeredUpdates.__iter__(self)

    def sprites(self) -> list[_GroupElement]:
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
        item: int | slice,
    ) -> _GroupElement | Sequence[_GroupElement]:
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
                try:
                    new_index = self._advance_input(index, event.button)
                except IndexError:
                    # Invalid move → stay where you are
                    return index

                index = new_index
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
        parent: RelativeGroup[Any] | Callable[[], Rect],
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
        bgd: Surface | None = None,
        special_flags: int = 0,
    ) -> list[FRect | Rect]:
        self.update_rect_from_parent()
        topleft = self.rect.topleft

        # The identity of the rectangle should be kept, as animations may
        # keep a reference to it
        for s in self.sprites():
            s.rect.move_ip(topleft)

        try:
            dirty = super().draw(surface=surface)
        finally:
            for s in self.sprites():
                s.rect.move_ip((-topleft[0], -topleft[1]))
        return dirty


class VisualSpriteList(RelativeGroup[_MenuElement]):
    """
    UI wrapper around GridIndexModel.

    Layout and movement semantics are defined in GridIndexModel.
    """

    orientation: Literal["horizontal", "vertical"] = "horizontal"
    rectangular: bool = False
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
        self.line_spacing: int | None = None
        self.max_width_per_column: int | None = None
        self.page_size: int | None = None
        self.current_page: int = 0

    @property
    def total_pages(self) -> int:
        if self.page_size is None:
            return 1

        # Count only slots that actually exist
        real_items = sum(1 for s in self.sprites() if s.enabled)
        return max(1, ceil(real_items / self.page_size))

    @property
    def has_next_page(self) -> bool:
        return (
            self.page_size is not None
            and self.current_page < self.total_pages - 1
        )

    @property
    def has_prev_page(self) -> bool:
        return self.page_size is not None and self.current_page > 0

    def set_page(self, page: int) -> None:
        if self.page_size is None:
            return
        self.current_page = max(0, min(page, self.total_pages - 1))
        self._needs_arrange = True

    def next_page(self) -> None:
        if self.has_next_page:
            self.current_page += 1
            self._needs_arrange = True

    def prev_page(self) -> None:
        if self.has_prev_page:
            self.current_page -= 1
            self._needs_arrange = True

    def next_page_wrap(self) -> None:
        if self.page_size is None:
            return
        self.current_page = (self.current_page + 1) % self.total_pages
        self._needs_arrange = True

    def prev_page_wrap(self) -> None:
        if self.page_size is None:
            return
        self.current_page = (self.current_page - 1) % self.total_pages
        self._needs_arrange = True

    def page_label(self) -> str:
        if self.page_size is None:
            return ""
        return f"{self.current_page + 1}/{self.total_pages}"

    def _index_model(self) -> GridIndexModel:
        return GridIndexModel(
            count=len(self),
            columns=self.columns,
            rectangular=self.rectangular,
            orientation=self.orientation,
        )

    @property
    def columns(self) -> int:
        return self._columns

    @columns.setter
    def columns(self, value: int) -> None:
        self._columns = value
        self._needs_arrange = True

    def _visible_indices(self) -> range:
        if self.page_size is None:
            return range(len(self))
        start = self.current_page * self.page_size
        end = start + self.page_size
        return range(start, min(end, len(self)))

    def snap_selection(self, old_index: int) -> int:
        visible = list(self._visible_indices())
        if not visible:
            return old_index

        sprites = self.sprites()
        enabled = {i: sprites[i].enabled for i in range(len(sprites))}

        first_visible = visible[0]
        first_enabled = next((i for i in visible if enabled[i]), None)

        if old_index in visible:
            # If the page contains any disabled items, the page’s
            # “primary enabled slot” wins.
            if any(not enabled[i] for i in visible):
                return (
                    first_enabled
                    if first_enabled is not None
                    else first_visible
                )

            # All items enabled → keep old_index
            return old_index

        # Special rule for page_size == 2:
        # Always snap to first_visible, even if disabled.
        if self.page_size == 2:
            return first_visible

        # General rule for other page sizes:
        # Snap to first enabled, else first visible.
        return first_enabled if first_enabled is not None else first_visible

    def calc_bounding_rect(self) -> Rect:
        if self._needs_arrange:
            self.arrange_menu_items()
        return super().calc_bounding_rect()

    def add(self, *sprites: PySprite | Any, **kwargs: Any) -> None:
        """
        Add something to the stacker.

        Do not add iterables to this function. Use 'extend'.

        Parameters:
            item: Stuff to add.
        """
        super().add(*sprites, **kwargs)
        self._needs_arrange = True

    def remove(self, *items: PySprite | Any) -> None:
        super().remove(*items)
        self._needs_arrange = True

    def clear_items(self) -> None:
        """Remove all sprites from this list."""
        self.empty()
        self._needs_arrange = True

    def draw(
        self,
        surface: Surface,
        bgd: Surface | None = None,
        special_flags: int = 0,
    ) -> list[FRect | Rect]:
        if self._needs_arrange:
            self.arrange_menu_items()
        dirty = super().draw(surface=surface)
        return dirty

    def arrange_menu_items(self) -> None:
        """
        Arrange sprites using LR semantics consistent with GridLayout.

        - Horizontal orientation → LR = row-major
        - Vertical orientation   → LR = column-major

        This ensures layout, movement, and LR/TB index transforms all agree.
        """
        if not len(self):
            return

        self.update_rect_from_parent()
        W, H = self.rect.size

        max_h = max(s.rect.height for s in self.sprites())
        max_w = max(s.rect.width for s in self.sprites())

        # Auto column calculation
        if self.max_width_per_column is not None:
            primary = W if self.orientation == "horizontal" else H
            self._columns = max(
                1, primary // max(1, self.max_width_per_column)
            )

        # Pagination: determine visible LR indices
        visible = list(self._visible_indices())
        if not visible:
            return

        visible_set = set(visible)
        for i, sprite in enumerate(self.sprites()):
            sprite.visible = i in visible_set

        start = visible[0]

        # Page-local model
        page_model = GridIndexModel(
            count=len(visible),
            columns=self.columns,
            rectangular=self.rectangular,
            orientation=self.orientation,
        )

        rows = page_model.layout.rows
        cols = self.columns

        # Line spacing
        if self.line_spacing is not None:
            line_spacing = self.line_spacing
        else:
            base = max_h if self.orientation == "horizontal" else max_w
            if self.expand:
                primary = H if self.orientation == "horizontal" else W
                line_spacing = primary // max(1, rows or 1)
            else:
                line_spacing = int(base * 1.2)

        # Column spacing
        column_spacing = (
            W // cols if self.orientation == "horizontal" else H // cols
        )

        for lr_index in visible:
            item = self.sprites()[lr_index]
            local_lr = lr_index - start
            row, col = page_model.lr_to_rowcol(local_lr)
            item.rect.topleft = (
                col * column_spacing,
                row * line_spacing,
            )

        self._needs_arrange = False

    def _allowed_input(self) -> Container[int]:
        return set(self._2d_movement_dict)

    def determine_cursor_movement(self, index: int, event: PlayerInput) -> int:
        """
        Move the cursor within the visible page, skipping disabled items.

        Differences from MenuSpriteGroup:
        - Movement is bounded to the current page (no cross-page jumps).
        - Disabled items are skipped by advancing again from the new position,
        not by re-advancing from the original position.
        - A boundary IndexError leaves the cursor on the last valid enabled item
        found during the walk, or on the original index if none was found.
        """
        if not len(self):
            return 0

        if not (event.pressed and event.button in self._allowed_input()):
            return index

        sprites = self.sprites()
        last_enabled = index

        candidate = index
        while True:
            try:
                candidate = self._advance_input(candidate, event.button)
            except IndexError:
                # Hit the grid boundary — stay at the last enabled position found
                return last_enabled

            if sprites[candidate].enabled:
                return candidate

            # Candidate is disabled — record nothing, keep walking
            # Guard against a full cycle with no enabled item
            if candidate == index:
                return last_enabled

    def _advance_input(self, index: int, button: int) -> int:
        index_type, incr = self._2d_movement_dict[button]

        # Orientation swap: vertical layout swaps LR↔TB semantics
        if self.orientation == "vertical":
            index_type = "tb" if index_type == "lr" else "lr"

        visible = list(self._visible_indices())
        local_index = visible.index(index)

        if self.rectangular:
            new_local = self._advance_rectangular(
                local_index, index_type, incr, visible
            )
        elif self.columns == 1 and index_type == "tb":
            new_local = self._advance_single_column(local_index, incr, visible)
        elif index_type == "tb":
            new_local = self._advance_ragged_tb(local_index, incr, visible)
        else:
            new_local = self._advance_ragged_lr(
                local_index, index_type, incr, visible
            )

        return visible[new_local]

    def _advance_rectangular(
        self, local_index: int, index_type: str, incr: int, visible: list[int]
    ) -> int:
        """Move within a fully padded rectangular virtual grid, wrapping at edges."""
        rows = ceil(len(visible) / self.columns)
        rect_model = GridIndexModel(
            count=rows * self.columns,
            columns=self.columns,
            rectangular=True,
            orientation=self.orientation,
        )
        new_virtual = rect_model.move_rectangular(
            local_index, index_type, incr
        )
        return new_virtual % len(visible)

    def _advance_single_column(
        self, local_index: int, incr: int, visible: list[int]
    ) -> int:
        """Simple wrapping movement for single-column lists."""
        return (local_index + incr) % len(visible)

    def _advance_ragged_tb(
        self, local_index: int, incr: int, visible: list[int]
    ) -> int:
        page_model = GridIndexModel(
            count=len(visible),
            columns=self.columns,
            rectangular=False,
            orientation=self.orientation,
        )
        tb = page_model.lr_to_tb(local_index)
        new_tb = tb + incr

        # Validate by round-tripping: if tb_to_lr gives a different column
        # than expected, or the result is out of range, the cell doesn't exist
        if new_tb < 0:
            raise IndexError

        new_lr = page_model.tb_to_lr(new_tb)

        # Verify the round-trip is consistent — invalid cells map to wrong columns
        if new_lr >= len(visible):
            raise IndexError
        if page_model.lr_to_tb(new_lr) != new_tb:
            raise IndexError

        return new_lr

    def _advance_ragged_lr(
        self, local_index: int, index_type: str, incr: int, visible: list[int]
    ) -> int:
        """
        LR movement in a ragged grid.
        Validates the destination cell exists — raises IndexError if not.
        """
        page_model = GridIndexModel(
            count=len(visible),
            columns=self.columns,
            rectangular=False,
            orientation=self.orientation,
        )
        new_local = page_model.move(local_index, index_type, incr)
        page_model.lr_to_rowcol(new_local)
        return new_local
