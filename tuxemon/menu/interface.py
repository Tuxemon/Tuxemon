# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic, TypeVar

from pygame import draw as pg_draw
from pygame.rect import Rect
from pygame.surface import Surface

from tuxemon.graphics import ColorLike, load_and_scale
from tuxemon.platform.const.graphics import (
    BLACK_COLOR,
    GFX_HP_BAR,
    GFX_XP_BAR,
    HP_COLOR_BG,
    HP_COLOR_FG,
    WHITE_COLOR,
    XP_COLOR_BG,
    XP_COLOR_FG,
)
from tuxemon.sprite import Sprite
from tuxemon.ui.graphic_box import GraphicBox

if TYPE_CHECKING:
    from tuxemon.prepare import DisplayContext


class Bar:
    """Common bar class for UI elements."""

    _graphics_cache: dict[str, Surface] = {}

    BASE_INNER_TOP_PADDING = 2
    BASE_INNER_BOTTOM_PADDING = 2
    BASE_INNER_LEFT_PADDING = 9
    BASE_INNER_RIGHT_PADDING = 2

    def __init__(
        self,
        context: DisplayContext,
        value: float,
        border_filename: str,
        fg_color: ColorLike = WHITE_COLOR,
        bg_color: ColorLike | None = BLACK_COLOR,
    ) -> None:
        """
        Initializes the bar with a given value, border filename, foreground color, and background color.

        Parameters:
            value: The initial value of the bar (clamped between 0.0 and 1.0).
            border_filename: The filename of the border image.
            fg_color: The foreground color of the bar.
            bg_color: The background color of the bar.
        """
        self.context = context
        self._value = max(0.0, min(1.0, value))
        self.border_filename = border_filename
        self.fg_color = fg_color
        self.bg_color = bg_color
        self.border: GraphicBox | None = None

        s = context.scaling.scale_int
        self.INNER_TOP_PADDING = s(self.BASE_INNER_TOP_PADDING)
        self.INNER_BOTTOM_PADDING = s(self.BASE_INNER_BOTTOM_PADDING)
        self.INNER_LEFT_PADDING = s(self.BASE_INNER_LEFT_PADDING)
        self.INNER_RIGHT_PADDING = s(self.BASE_INNER_RIGHT_PADDING)

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
            image = self._graphics_cache[self.border_filename]
        else:
            image = load_and_scale(self.border_filename)
            self._graphics_cache[self.border_filename] = image

        self.border = GraphicBox(Rect(0, 0, 1, 1), image)

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
        bg_color: ColorLike | None = None,
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

    def __init__(self, context: DisplayContext, value: float = 1.0) -> None:
        """
        Initializes the HP bar with a given value.

        Parameters:
            value: The initial value of the HP bar.
        """
        super().__init__(
            context,
            max(0.0, min(1.0, value)),
            GFX_HP_BAR,
            HP_COLOR_FG,
            HP_COLOR_BG,
        )


class ExpBar(Bar):
    """EXP bar for UI elements."""

    def __init__(self, context: DisplayContext, value: float = 1.0) -> None:
        """
        Initializes the EXP bar with a given value.

        Parameters:
            value: The initial value of the EXP bar.
        """
        super().__init__(
            context,
            max(0.0, min(1.0, value)),
            GFX_XP_BAR,
            XP_COLOR_FG,
            XP_COLOR_BG,
        )


T = TypeVar("T", covariant=True)


class MenuItem(Generic[T], Sprite):
    """
    Represents a selectable item within a user interface menu.

    A MenuItem is a visual component used to represent an option in a menu.
    It can display an image, label, and description, and is associated with
    a callable game object or behavior that is triggered when selected.
    """

    def __init__(
        self,
        image: Surface | None,
        label: str | None,
        description: str | None,
        game_object: T,
        enabled: bool = True,
        position: tuple[int, int] | None = None,
    ):
        super().__init__(image=image)

        self.label = label
        self.description = description
        self.game_object = game_object

        self._enabled = enabled
        self._in_focus = False

        self.metadata: dict[str, Any] = {}

        if position is not None:
            self.set_position(*position)

        self.update_image()

    def trigger(self) -> None:
        """Triggers the associated action for this menu item."""
        if not self._enabled:
            return

        action = self.game_object

        # Legacy callable
        if callable(action):
            action()

    def update_image(self, source: Surface | None = None) -> None:
        """
        Update the image of the sprite, applying focus/enabled visual changes.
        """
        super().update_image(source=source)

        if self._image is None:
            return

        if self._in_focus:
            pass  # Add highlight, tint, outline, etc.

        if not self._enabled:
            pass  # Add dimming, greyscale, alpha reduction, etc.

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        if self._enabled != value:
            self._enabled = value
            self.update_image()

    @property
    def in_focus(self) -> bool:
        return self._in_focus

    @in_focus.setter
    def in_focus(self, value: bool) -> None:
        if self._in_focus != value:
            self._in_focus = value
            self.update_image()

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} at 0x{id(self):x} "
            f"label={self.label!r}, enabled={self.enabled}>"
        )
