# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from typing import ClassVar, Generic, Optional, TypeVar

import pygame

from tuxemon import graphics, tools
from tuxemon.sprite import Sprite
from tuxemon.ui.draw import GraphicBox


class Bar:
    """Common bar class for UI elements."""

    border_filename: ClassVar[str]
    border = None  # type: ClassVar[GraphicBox]
    fg_color: ClassVar[graphics.ColorLike] = (255, 255, 255)
    bg_color: ClassVar[Optional[graphics.ColorLike]] = (0, 0, 0)

    def __init__(self, value: float = 1.0) -> None:
        if self.border is None:
            self.load_graphics()

        self.value = value

    def load_graphics(self) -> None:
        """
        Load the border image.

        Image become class attribute, so is shared.
        Eventually, implement some game-wide image caching.
        """
        image = graphics.load_and_scale(self.border_filename)
        type(self).border = GraphicBox(image)

    @staticmethod
    def calc_inner_rect(rect: pygame.rect.Rect) -> pygame.rect.Rect:
        """
        Calculate inner rectangle.

        Calculate the inner rect to draw fg_color that fills bar
        The values here are calculated based on game scale and
        the content of the border image file.

        Parameters:
            rect: Outside rectangle.

        Returns:
            Inner rectangle.

        """
        inner = rect.copy()
        inner.top += tools.scale(2)
        inner.height -= tools.scale(4)
        inner.left += tools.scale(9)
        inner.width -= tools.scale(11)
        return inner

    def draw(
        self,
        surface: pygame.surface.Surface,
        rect: pygame.rect.Rect,
    ) -> None:
        """
        Draws the bar.

        Parameters:
            surface: Surface where to draw the bar.
            rect: Location and size of the bar.

        """
        inner = self.calc_inner_rect(rect)
        if self.bg_color is not None:
            pygame.draw.rect(surface, self.bg_color, inner)
        if self.value > 0:
            inner.width = int(inner.width * self.value)
            pygame.draw.rect(surface, self.fg_color, inner)
        self.border.draw(surface, rect)


class HpBar(Bar):
    """HP bar for UI elements."""

    border_filename = "gfx/ui/monster/hp_bar.png"
    border = None  # type: ClassVar[GraphicBox]
    fg_color = (10, 240, 25)
    bg_color = (245, 10, 25)


class ExpBar(Bar):
    """EXP bar for UI elements."""

    border_filename = "gfx/ui/monster/exp_bar.png"
    border = None  # type: ClassVar[GraphicBox]
    fg_color = (31, 239, 255)
    bg_color = None


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
    ):
        super().__init__()
        self.image = image
        self.rect = image.get_rect() if image else pygame.rect.Rect(0, 0, 0, 0)
        self.label = label
        self.description = description
        self.game_object = game_object

        self.enabled = True
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
