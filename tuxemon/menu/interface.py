# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from typing import Generic, Optional, TypeVar

import pygame

from tuxemon import graphics, prepare, tools
from tuxemon.sprite import Sprite
from tuxemon.ui.draw import GraphicBox


class Bar:
    """Common bar class for UI elements."""

    _graphics_cache: dict[str, pygame.surface.Surface] = {}

    def __init__(
        self,
        value: float,
        border_filename: str,
        fg_color: graphics.ColorLike = prepare.WHITE_COLOR,
        bg_color: Optional[graphics.ColorLike] = prepare.BLACK_COLOR,
    ) -> None:
        """
        Initializes the bar with a given value, border filename, foreground color, and background color.

        Parameters:
            value: The initial value of the bar.
            border_filename: The filename of the border image.
            fg_color: The foreground color of the bar.
            bg_color: The background color of the bar.
        """
        self.value = value
        self.border_filename = border_filename
        self.fg_color = fg_color
        self.bg_color = bg_color
        self.border: Optional[GraphicBox] = None

    def load_graphics(self) -> None:
        """
        Loads the border image.
        """
        if self.border_filename in self._graphics_cache:
            self.border = GraphicBox(
                self._graphics_cache[self.border_filename]
            )
        else:
            image = graphics.load_and_scale(self.border_filename)
            self.border = GraphicBox(image)
            self._graphics_cache[self.border_filename] = image

    def calc_inner_rect(self, rect: pygame.rect.Rect) -> pygame.rect.Rect:
        """
        Calculates the inner rectangle of the bar.

        Parameters:
            rect: The outer rectangle of the bar.

        Returns:
            The inner rectangle of the bar.
        """
        INNER_TOP_PADDING = tools.scale(2)
        INNER_BOTTOM_PADDING = tools.scale(2)
        INNER_LEFT_PADDING = tools.scale(9)
        INNER_RIGHT_PADDING = tools.scale(2)

        inner = rect.copy()
        inner.top += INNER_TOP_PADDING
        inner.height -= INNER_TOP_PADDING + INNER_BOTTOM_PADDING
        inner.left += INNER_LEFT_PADDING
        inner.width -= INNER_LEFT_PADDING + INNER_RIGHT_PADDING
        return inner

    def draw(
        self, surface: pygame.surface.Surface, rect: pygame.rect.Rect
    ) -> None:
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
        if self.bg_color is not None:
            pygame.draw.rect(surface, self.bg_color, inner)
        if self.value > 0:
            inner.width = int(inner.width * self.value)
            pygame.draw.rect(surface, self.fg_color, inner)
        self.border.draw(surface, rect)

    def set_color(
        self,
        fg_color: graphics.ColorLike,
        bg_color: Optional[graphics.ColorLike] = None,
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
    Item from a menu.

    Parameters:
        image: Image of the menu item.
        label: Name of the menu item.
        description: Description of the menu item.
        game_object: Callable used when the menu item is selected.

    """

    def __init__(
        self,
        image: pygame.surface.Surface,
        label: Optional[str],
        description: Optional[str],
        game_object: T,
        enabled: bool = True,
    ):
        super().__init__()
        self.image = image
        self.rect = image.get_rect() if image else pygame.rect.Rect(0, 0, 0, 0)
        self.label = label
        self.description = description
        self.game_object = game_object
        self.enabled = enabled

        self._in_focus = False

    def toggle_focus(self) -> None:
        """Toggles the focus of the menu item."""
        self._in_focus = not self._in_focus

    @property
    def in_focus(self) -> bool:
        return self._in_focus

    @in_focus.setter
    def in_focus(self, value: bool) -> None:
        self._in_focus = bool(value)

    def __repr__(self) -> str:
        return f"MenuItem({self.label}, {self.description}, image={self.image}, enabled={self.enabled})"


class MenuCursor(Sprite):
    """
    Menu cursor.

    Typically it is an arrow that shows the currently selected menu item.

    Parameters:
        image: Image that represents the cursor.
    """

    def __init__(self, image: pygame.surface.Surface) -> None:
        super().__init__()
        self.image = image
        self.rect = image.get_rect()
