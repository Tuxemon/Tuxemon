# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Generic, Optional, TypeVar

from pygame.surface import Surface

from tuxemon.graphics import load_and_scale
from tuxemon.sprite import Sprite
from tuxemon.tools import scale

if TYPE_CHECKING:
    from tuxemon.animation import Animation
    from tuxemon.menu.interface import MenuItem
    from tuxemon.sprite import SpriteGroup

T = TypeVar("T", covariant=True)

CURSOR_X_RATIO_DENOMINATOR: float = 2.727
CURSOR_Y_RATIO_DENOMINATOR: float = 10.0


class MenuCursor(Sprite):
    """
    Visual indicator for the currently selected menu item.

    Typically rendered as an arrow or icon, the MenuCursor tracks the selected item
    in a menu interface. It supports optional pixel offsets to fine-tune its position
    relative to the target item.

    Inherits from:
        Sprite: Provides image, rect, and positioning logic.

    Parameters:
        image: The visual representation of the cursor.
        x_offset: Horizontal offset from the anchor point. Defaults to 0.
        y_offset: Vertical offset from the anchor point. Defaults to 0.
    """

    def __init__(
        self, image: Surface, x_offset: int = 0, y_offset: int = 0
    ) -> None:
        super().__init__(image=image)
        self.x_offset = x_offset
        self.y_offset = y_offset


class MenuCursorController(Generic[T]):
    """
    Manages display and behavior of the cursor in a menu interface,
    including visibility, movement, and selection focus.
    """

    def __init__(
        self,
        cursor_filename: str,
        menu_sprites: SpriteGroup[MenuCursor],
        get_selected_item: Callable[[], Optional[MenuItem[T]]],
        animate: Callable[..., Animation],
        duration: float,
        remove_animations: Callable[[Any], None],
        offset: tuple[int, int] = (0, 0),
        cursor_image: Optional[Surface] = None,
    ):
        """
        Initializes the cursor controller with required graphics
        and logic hooks.

        Parameters:
            cursor_filename: Path to the cursor image.
            menu_sprites: Group containing menu-related sprites.
            get_selected_item: Function to retrieve the currently
                selected menu item.
            animate: Function to trigger animations.
            duration: Time in seconds for cursor movement animation.
            remove_animations: Function to clear existing animations
                for a given target.
            offset: Tuple for (x, y) pixel offset to adjust cursor position
                relative to the menu item.
            cursor_image: Optional preloaded Surface to override image loading.
                Useful for testing or dynamic cursor theming.
        """
        image = cursor_image or load_and_scale(cursor_filename)
        x_off, y_off = offset
        self.arrow = MenuCursor(image, x_off, y_off)
        self.sprites = menu_sprites
        self.get_item = get_selected_item
        self.animate = animate
        self.duration = duration
        self.remove_animations = remove_animations

    def get_margin(self) -> tuple[int, int]:
        """
        Calculates margin using ratios derived from the original hardcoded scale values.
        Keeps layout behavior consistent with (-scale(11), -scale(5)).
        """
        x = -scale(
            int(self.arrow.image.get_width() / CURSOR_X_RATIO_DENOMINATOR)
        )
        y = -scale(
            int(self.arrow.image.get_height() / CURSOR_Y_RATIO_DENOMINATOR)
        )
        return (x, y)

    def show_cursor(self) -> None:
        """Makes the cursor visible and updates its position and focus state."""
        self._ensure_cursor_visible(True)

    def hide_cursor(self) -> None:
        """Hides the cursor and clears focus from the selected item."""
        self._ensure_cursor_visible(False)

    def _ensure_cursor_visible(self, visible: bool) -> None:
        """
        Adds or removes the cursor from the sprite group and updates item focus.

        Parameters:
            visible: True to show the cursor, False to hide it.
        """
        if visible:
            if self.arrow not in self.sprites:
                self.sprites.add(self.arrow)
        else:
            if self.arrow in self.sprites:
                self.sprites.remove(self.arrow)

        self._update_focus(self.get_item(), visible)
        if visible:
            self.trigger_cursor_update(animate=False)

    def _update_focus(self, item: Optional[MenuItem[T]], focus: bool) -> None:
        """
        Sets the focus state on a menu item and refreshes its appearance.

        Parameters:
            item: Menu item to update.
            focus: True to apply focus, False to remove it.
        """
        if item:
            item.in_focus = focus
            item.update_image()

    def trigger_cursor_update(
        self, animate: bool = True
    ) -> Optional[Animation]:
        """
        Moves the cursor to match the selected menu item's position.

        Parameters:
            animate: If True, cursor movement is animated.

        Returns:
            An animation object if animated, or None.
        """
        item = self.get_item()
        if not item:
            return None

        x, y = item.rect.midleft
        x -= scale(2)

        if animate:
            self.remove_animations(self.arrow.rect)
            return self.animate(
                self.arrow.rect,
                right=x,
                centery=y,
                duration=self.duration,
            )
        else:
            self.arrow.rect.midright = (x, y)
            return None

    def update_selection_focus(
        self,
        previous_item: Optional[MenuItem[T]],
        new_item: Optional[MenuItem[T]],
    ) -> None:
        """
        Handles transition of focus between menu items and updates cursor
        position.

        Parameters:
            previous_item: The menu item that was previously focused.
            new_item: The newly selected menu item.
        """
        self._update_focus(previous_item, False)
        self._update_focus(new_item, True)
        self.trigger_cursor_update(animate=True)
