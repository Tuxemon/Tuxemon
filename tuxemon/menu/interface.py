# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from typing import Generic, Optional, TypeVar

from pygame import draw as pg_draw
from pygame.rect import Rect
from pygame.surface import Surface

from tuxemon import prepare, tools
from tuxemon.graphics import ColorLike, load_and_scale
from tuxemon.sprite import Sprite
from tuxemon.ui.graphic_box import GraphicBox


class Bar:
    """Common bar class for UI elements."""

    _graphics_cache: dict[str, Surface] = {}
    INNER_TOP_PADDING = tools.scale(2)
    INNER_BOTTOM_PADDING = tools.scale(2)
    INNER_LEFT_PADDING = tools.scale(9)
    INNER_RIGHT_PADDING = tools.scale(2)

    def __init__(
        self,
        value: float,
        border_filename: str,
        fg_color: ColorLike = prepare.WHITE_COLOR,
        bg_color: Optional[ColorLike] = prepare.BLACK_COLOR,
    ) -> None:
        """
        Initializes the bar with a given value, border filename, foreground color, and background color.

        Parameters:
            value: The initial value of the bar (clamped between 0.0 and 1.0).
            border_filename: The filename of the border image.
            fg_color: The foreground color of the bar.
            bg_color: The background color of the bar.
        """
        self._value = 0.0
        self.value = value
        self.border_filename = border_filename
        self.fg_color = fg_color
        self.bg_color = bg_color
        self.border: Optional[GraphicBox] = None

    @property
    def value(self) -> float:
        """Gets the current value of the bar."""
        return self._value

    @value.setter
    def value(self, new_value: float) -> None:
        """Sets the value of the bar with clamping between 0.0 and 1.0."""
        self._value = max(0.0, min(1.0, new_value))

    def load_graphics(self) -> None:
        """Loads the border image."""
        if self.border_filename in self._graphics_cache:
            self.border = GraphicBox(
                self._graphics_cache[self.border_filename]
            )
        else:
            image = load_and_scale(self.border_filename)
            self.border = GraphicBox(image)
            self._graphics_cache[self.border_filename] = image

    def calc_inner_rect(self, rect: Rect) -> Rect:
        """
        Calculates the inner rectangle of the bar.

        Parameters:
            rect: The outer rectangle of the bar.

        Returns:
            The inner rectangle of the bar.
        """
        inner = rect.copy()
        inner.top += self.INNER_TOP_PADDING
        inner.height -= self.INNER_TOP_PADDING + self.INNER_BOTTOM_PADDING
        inner.left += self.INNER_LEFT_PADDING
        inner.width -= self.INNER_LEFT_PADDING + self.INNER_RIGHT_PADDING
        return inner

    def draw(self, surface: Surface, rect: Rect) -> None:
        """
        Draws the bar on a given surface at a specified location and size.

        Parameters:
            surface: The surface to draw the bar on.
            rect: The location and size of the bar.
        """
        if self.border is None:
            self.load_graphics()
            if self.border is None:
                raise ValueError("Failed to load border graphics")

        inner = self.calc_inner_rect(rect)
        if self.bg_color:
            pg_draw.rect(surface, self.bg_color, inner)
        if self.value > 0:
            inner.width = int(inner.width * self.value)
            pg_draw.rect(surface, self.fg_color, inner)
        self.border.draw(surface, rect)

    def set_color(
        self,
        fg_color: ColorLike,
        bg_color: Optional[ColorLike] = None,
    ) -> None:
        """
        Sets the foreground and background colors of the bar.

        Parameters:
            fg_color: The new foreground color of the bar.
            bg_color: The new background color of the bar. If None, the
                background color remains unchanged.
        """
        self.fg_color = fg_color
        if bg_color is not None:
            self.bg_color = bg_color


class HpBar(Bar):
    """HP bar for UI elements."""

    def __init__(self, value: float = 1.0) -> None:
        """
        Initializes the HP bar with a given value.

        Parameters:
            value: The initial value of the HP bar.
        """
        super().__init__(
            value, prepare.GFX_HP_BAR, prepare.HP_COLOR_FG, prepare.HP_COLOR_BG
        )


class ExpBar(Bar):
    """EXP bar for UI elements."""

    def __init__(self, value: float = 1.0) -> None:
        """
        Initializes the EXP bar with a given value.

        Parameters:
            value: The initial value of the EXP bar.
        """
        super().__init__(
            value, prepare.GFX_XP_BAR, prepare.XP_COLOR_FG, prepare.XP_COLOR_BG
        )


T = TypeVar("T", covariant=True)


class MenuItem(Generic[T], Sprite):
    """
    Represents a selectable item within a user interface menu.

    A MenuItem is a visual component used to represent an option in a menu.
    It can display an image, label, and description, and is associated with
    a callable game object or behavior that is triggered when selected.

    Inherits from:
        Sprite: Provides rendering, animation, and position management.

    Type Parameters:
        T: The type of the game object or callable associated with this item.

    Parameters:
        image: The visual surface to represent the item.
        label: A short label or name for the menu item.
        description: A longer description or tooltip text.
        game_object: A callable or linked object triggered on selection.
        enabled: Whether the menu item is interactable. Defaults to True.
        position: Initial (x, y) position of the item.
            If None, position must be set later. Defaults to None.
    """

    def __init__(
        self,
        image: Optional[Surface],
        label: Optional[str],
        description: Optional[str],
        game_object: T,
        enabled: bool = True,
        position: Optional[tuple[int, int]] = None,
    ):
        super().__init__(image=image)
        self.label = label
        self.description = description
        self.game_object = game_object
        self._enabled = enabled
        self._in_focus = False

        if position is not None:
            self.set_position(*position)

        self.update_image()

    def update_image(self) -> None:
        """
        Update the image of the sprite, applying focus/enabled visual changes.
        """
        super().update_image()

        if self._image is None:
            return

        if self._in_focus:
            # Add visual effect for focus here
            pass

        if not self._enabled:
            # Add visual effect for not enabled here
            pass

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        if self._enabled != value:
            self._enabled = value

    @property
    def in_focus(self) -> bool:
        return self._in_focus

    @in_focus.setter
    def in_focus(self, value: bool) -> None:
        self._in_focus = bool(value)

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} at 0x{id(self):x} "
            f"label={self.label!r}, enabled={self.enabled}>"
        )


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
