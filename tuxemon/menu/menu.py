# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from functools import partial
from typing import Any, ClassVar, Generic, Optional, TypeVar, Union

import pygame_menu
from pygame.font import Font
from pygame.rect import Rect
from pygame.surface import Surface
from pygame_menu import baseimage, locals, themes
from pygame_menu.widgets.core.widget import Widget

from tuxemon import graphics, prepare, tools
from tuxemon.animation import Animation, ScheduleType
from tuxemon.constants.asset_loader import fetch_asset
from tuxemon.graphics import ColorLike
from tuxemon.menu.alert import AlertManager
from tuxemon.menu.controller import MenuController
from tuxemon.menu.cursor import MenuCursor, MenuCursorController
from tuxemon.menu.events import playerinput_to_event
from tuxemon.menu.interface import MenuItem
from tuxemon.menu.theme import get_sound_engine, get_theme
from tuxemon.platform.const import buttons, intentions
from tuxemon.platform.events import PlayerInput
from tuxemon.sprite import (
    RelativeGroup,
    SpriteGroup,
    VisualSpriteList,
)
from tuxemon.state.state import State
from tuxemon.ui.graphic_box import GraphicBox
from tuxemon.ui.text_renderer import TextRenderer

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FontSettings:
    smaller: int = prepare.SCALE * prepare.FONT_SIZE_SMALLER
    small: int = prepare.SCALE * prepare.FONT_SIZE_SMALL
    medium: int = prepare.SCALE * prepare.FONT_SIZE
    big: int = prepare.SCALE * prepare.FONT_SIZE_BIG
    bigger: int = prepare.SCALE * prepare.FONT_SIZE_BIGGER
    biggest: int = prepare.SCALE * prepare.FONT_SIZE_BIGGEST


T = TypeVar("T", covariant=True)


class PygameMenuState(State):
    """
    A Pygame menu state class.
    """

    name: ClassVar[str] = "PygameMenuState"
    transparent = True

    def __init__(
        self,
        width: int = 1,
        height: int = 1,
        theme: Optional[pygame_menu.Theme] = None,
        sound_engine: Optional[pygame_menu.Sound] = None,
        font_settings: Optional[FontSettings] = None,
        **kwargs: Any,
    ) -> None:
        self.font_type = font_settings or FontSettings()
        super().__init__()
        theme = theme or get_theme()
        self._initialize_attributes()
        self._create_menu(width, height, theme, sound_engine, **kwargs)

    def _initialize_attributes(self) -> None:
        """
        Initializes the attributes of the menu state.

        Parameters:
            theme: The theme of the menu.
        """
        self.state_controller = MenuController()
        self.open = False
        self.escape_key_exits = True
        self.selected_widget: Optional[Widget] = None

    def _create_menu(
        self,
        width: int,
        height: int,
        theme: pygame_menu.Theme,
        sound_engine: Optional[pygame_menu.Sound],
        **kwargs: Any,
    ) -> None:
        """
        Creates the Pygame menu.

        Parameters:
            width: The width of the menu.
            height: The height of the menu.
            theme: The theme of the menu.
            sound_engine: Optional pre-configured sound engine.
        """
        self.menu = pygame_menu.Menu(
            "",
            width,
            height,
            theme=theme,
            center_content=True,
            onclose=self._on_close,
            **kwargs,
        )

        if sound_engine is None:
            sound_file = self.client.sound_manager.get_sound_filename(
                prepare.CONFIG.menu_sound
            )
            sound_volume = self.client.config.sound_volume
            sound_engine = get_sound_engine(sound_volume, sound_file)

        self.menu.set_sound(sound_engine)
        # If we 'ignore nonphysical keyboard', pygame_menu will check the
        # pygame event queue to make sure there is an actual keyboard event
        # being pressed right now, and ignore the event if not, hence it won't
        # work for controllers.
        self.menu._keyboard_ignore_nonphysical = False

    def _setup_theme(
        self, background: str, position: str = locals.POSITION_CENTER
    ) -> themes.Theme:
        """
        Sets up a Pygame menu theme with a custom background image.

        Parameters:
            background: The path to the background image file.
            position: The position of the background image.

        Returns:
            pygame_menu.Theme: The configured theme object.
        """
        base_image = self._create_image(background, position)
        theme = get_theme()
        theme.background_color = base_image
        return theme

    def _create_image(
        self, path: str, position: str = locals.POSITION_CENTER
    ) -> baseimage.BaseImage:
        """
        Creates a Pygame menu image.

        Parameters:
            path: The path to the background image file.
            position: The position of the background image.

        Returns:
            pygame_menu.BaseImage: The created background image object.
        """
        return pygame_menu.BaseImage(
            image_path=tools.transform_resource_filename(path),
            drawing_position=position,
        )

    def update_selected_widget(self) -> None:
        """
        Updates the currently selected widget based on the menu's selection.
        """
        self.selected_widget = self.menu.get_selected_widget()

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        """
        Processes a player input event.

        Parameters:
            event: The player input event.

        Returns:
            Optional[PlayerInput]: The processed event or None if it's not handled.
        """
        if (
            not self.state_controller.is_interactive()
            or not self.menu.is_enabled()
        ):
            return event

        if (
            event.button in {buttons.B, buttons.BACK, intentions.MENU_CANCEL}
            and not self.escape_key_exits
        ):
            return None

        try:
            pygame_event = playerinput_to_event(event)
            if self.open and event.pressed and pygame_event is not None:
                self.menu.update([pygame_event])
                self.selected_widget = self.menu.get_selected_widget()
        except Exception as e:
            logger.error(f"Unexpected error in menu event processing: {e}")
        return event if pygame_event is None else None

    def draw(self, surface: Surface) -> None:
        """
        Draws the menu on the given surface.

        Parameters:
            surface: The surface to draw on.
        """
        if not self.state_controller.is_closed() and self.menu.is_enabled():
            self.menu.draw(surface)

    def _set_open(self) -> None:
        """
        Sets the menu as open.
        """
        self.open = True
        self.state_controller.set_normal()
        self.menu.enable()

    def resume(self) -> None:
        """
        Resumes the menu.
        """
        if self.state_controller.is_closed():
            self.state_controller.open()
            animation = self.animate_open()
            if animation:
                animation.schedule(self._set_open, ScheduleType.ON_FINISH)
            else:
                self._set_open()
        else:
            logger.debug(
                f"resume() called, but menu already in state {self.state_controller.state.name}"
            )

    def disable(self) -> None:
        """
        Disables the menu, preventing interaction but still allowing drawing.
        """
        if self.state_controller.is_enabled():
            self.state_controller.disable()
            self.menu.disable()
        else:
            logger.debug("Menu disable called but was not in NORMAL state.")

    def enable(self) -> None:
        """
        Enables the menu, allowing interaction again.
        """
        if self.state_controller.is_disabled():
            self.state_controller.set_normal()
            self.menu.enable()
        else:
            logger.debug("Menu enable called but was not in DISABLED state.")

    def _on_close(self) -> None:
        """
        Called when the menu is closed.
        """
        self.open = False
        self.state_controller.close()
        self.reset_theme()
        self.menu.disable()
        self.selected_widget = None

        animation = self.animate_close()
        if animation:
            animation.schedule(self.client.pop_state, ScheduleType.ON_FINISH)
        else:
            self.client.pop_state()

    def _finalize(self) -> None:
        """
        Final cleanup before the menu state is fully closed.
        """
        self.menu.disable()
        self.menu.clear()
        self.selected_widget = None
        self.open = False

    def reset_theme(self) -> None:
        """Reset to original theme (color, alignment, etc.)"""
        theme = get_theme()
        theme.scrollarea_position = locals.SCROLLAREA_POSITION_NONE
        theme.background_color = prepare.BACKGROUND_COLOR
        theme.widget_alignment = locals.ALIGN_LEFT
        theme.title = False

    def animate_open(self) -> Optional[Animation]:
        """
        Animates the menu opening.

        Returns:
            Optional[Animation]: The animation or None if not implemented.
        """
        return None

    def animate_close(self) -> Optional[Animation]:
        """
        Animates the menu closing.

        Returns:
            Optional[Animation]: The animation or None if not implemented.
        """
        return None


class Menu(Generic[T], State):
    """
    A class to create menu objects.

    Menus are a type of game state.  Menus that are the top state
    will receive player input and respond to it.  They may be
    stacked, so that menus are nested.

    Attributes:
        rect: The rect of the menu in pixels, defaults to 0, 0, 400, 200.
        state: An arbitrary state of the menu. E.g. MenuState.OPENING or MenuState.CLOSING.
        selected_index: The index position of the currently selected menu item.
        menu_items: A list of available menu items.
    """

    name: ClassVar[str] = "Menu"
    # defaults for the menu
    columns = 1
    min_font_size = 4
    draw_borders = True
    background = None  # Image used to draw the background
    # The window's background color
    background_color: ColorLike = prepare.BACKGROUND_COLOR
    font_color: ColorLike = prepare.FONT_COLOR
    font_shadow_color: ColorLike = prepare.FONT_SHADOW_COLOR
    # Font color when the action is unavailable
    unavailable_color: ColorLike = prepare.UNAVAILABLE_COLOR
    unavailable_color_shop: ColorLike = prepare.UNAVAILABLE_COLOR_SHOP
    # File to load for image background
    background_filename: Optional[str] = None
    menu_select_sound_filename = prepare.CONFIG.menu_sound
    font_filename = prepare.CONFIG.locale.font_file
    borders_filename = prepare.CONFIG.menu_border
    cursor_filename = prepare.CONFIG.menu_cursor
    cursor_move_duration = 0.20
    shrink_to_items = False  # fit the border to contents
    escape_key_exits = True  # escape key closes menu
    animate_contents = False  # show contents while window opens
    # if true, then menu items can be selected with the mouse/touch
    touch_aware = True

    def __init__(self, selected_index: int = 0, **kwargs: Any) -> None:
        super().__init__()

        self.rect = self.rect.copy()  # do not remove!
        self.selected_index = selected_index
        # state: closed, opening, normal, disabled, closing
        self.state_controller = MenuController()
        self._show_contents = False
        self._needs_refresh = False
        self.dialog = AlertManager(self.sprites, self.task)
        self._anchors: dict[str, Union[int, tuple[int, int]]] = {}
        self.__dict__.update(kwargs)

        # holds sprites representing menu items
        self.create_new_menu_items_group()

        # callbacks
        self.on_close_callback: Optional[Callable[[], None]] = None
        self.on_menu_selection_change_callback: Optional[
            Callable[[], None]
        ] = None

        self.font_filename = fetch_asset("font", self.font_filename)
        self.font = self.set_font()  # load default font
        self.load_graphics()  # load default graphics
        self.reload_sounds()  # load default sounds
        self._input_handler: InputHandler = MenuInputHandler(self)
        self._text_renderer = TextRenderer(
            font=self.font,
            font_filename=self.font_filename,
            font_color=self.font_color,
            font_shadow_color=self.font_shadow_color,
        )

        self.cursor_controller: MenuCursorController[T] = MenuCursorController(
            cursor_filename=self.cursor_filename,
            menu_sprites=self.menu_sprites,
            get_selected_item=self.get_selected_item,
            animate=self.animate,
            duration=self.cursor_move_duration,
            remove_animations=self.remove_animations_of,
        )

    def set_input_handler(self, handler: InputHandler) -> None:
        """
        Sets a new input handler for the menu, enabling dynamic replacement
        of input processing logic.
        """
        self._input_handler = handler

    def create_new_menu_items_group(self) -> None:
        """
        Create a new group for menu items to be contained in.

        Override if you need special placement for the menu items.
        """
        # contains the selectable elements of the menu
        self.menu_items: VisualSpriteList[MenuItem[T]] = VisualSpriteList(
            parent=self.calc_menu_items_rect,
        )
        self.menu_items.columns = self.columns

        # generally just for the cursor arrow
        self.menu_sprites: SpriteGroup[MenuCursor] = RelativeGroup(
            parent=self.menu_items,
        )

    def shutdown(self) -> None:
        """Clear objects likely to cause cyclical references."""
        self.sprites.empty()
        self.menu_items.empty()
        self.menu_sprites.empty()
        self.animations.empty()

        self.client.event_manager.release_controls(self.client.input_manager)

        del self.menu_items
        del self.menu_sprites
        del self.cursor_controller

    def initialize_items(self) -> Optional[Iterable[MenuItem[T]]]:
        """
        Advanced way to fill in menu items.

        For menus that change dynamically, use of this method will
        make changes to the menu easier.
        """

    def is_valid_entry(self, game_object: Any) -> bool:
        """
        Checked when items are loaded/reloaded.

        The return value will enable/disable menu items.

        WIP.  The value passed should be Item.game_object.

        Parameters:
            game_object: Any object to check.

        Returns:
            Becomes the menu item enabled value.
        """
        return True

    def reload_items(self) -> None:
        """
        Empty all items in the menu and re-add them.
        Only works if initialize_items is used.
        """
        self._needs_refresh = True
        items = self.initialize_items()

        if not items:
            return

        self.menu_items.empty()

        for item in items:
            self.add(item)
            if item.enabled:
                item.enabled = self.is_valid_entry(item.game_object)

        self.menu_items.arrange_menu_items()

        selected_item = self.get_selected_item()
        if selected_item and selected_item.enabled:
            return

        # Choose new cursor position. We can't use the prev position, so we
        # will use the closest valid option.
        score = None
        prev_index = self.selected_index
        for index, item in enumerate(self.menu_items):
            if item.enabled:
                new_score = abs(prev_index - index)
                if score is None or new_score < score:
                    self.selected_index = index
                    score = new_score

    def build_item(
        self: Menu[Callable[[], object]],
        label: str,
        callback: Callable[[], object],
        icon: Optional[Surface] = None,
    ) -> None:
        """
        Create a menu item and add it to the menu.

        Parameters:
            label: Some text.
            callback: Callback to use when selected.
            icon: Image of the item (not used yet).
        """
        image = self.shadow_text(label)
        item = MenuItem(image, label, None, callback)
        self.add(item)

    def add(self, menu_item: MenuItem[T]) -> None:
        """
        Add a menu item.

        Parameters:
            menu_item: Menu item to add.
        """
        self.menu_items.add(menu_item)
        self._needs_refresh = True

    def clear(self) -> None:
        """Clears all menu items."""
        self.menu_items.clear()
        self._needs_refresh = True

    def fit_border(self) -> None:
        """Resize the window border to fit the contents of the menu."""
        # get bounding box of menu items and the cursor
        center = self.rect.center
        rect1 = self.menu_items.calc_bounding_rect()
        rect2 = self.menu_sprites.calc_bounding_rect()
        rect1 = rect1.union(rect2)

        # expand the bounding box by the border and some padding
        # TODO: do not hardcode these values
        # border is 12, padding is the rest
        rect1.width += tools.scale(18)
        rect1.height += tools.scale(19)
        rect1.topleft = 0, 0

        # set our rect and adjust the centers to match
        self.rect = rect1
        self.rect.center = center

        # move the bounding box taking account the anchors
        self.position_rect()

    def reload_sounds(self) -> None:
        """Reload sounds."""
        self.menu_select_sound = self.client.sound_manager.load_sound(
            self.menu_select_sound_filename
        )

    def shadow_text(
        self,
        text: str,
        bg: ColorLike = font_shadow_color,
        fg: Optional[ColorLike] = None,
        offset: tuple[float, float] = (0.5, 0.5),
    ) -> Surface:
        """Renders text with a drop shadow using the configured text renderer."""
        return self._text_renderer.shadow_text(text, bg, fg, offset)

    def load_graphics(self) -> None:
        """
        Loads all the graphical elements of the menu.

        Will load some elements from disk, so needs to be called at least once.
        """
        if not self.transparent:
            # load and scale the _background
            background = None
            if self.background_filename:
                background = graphics.load_image(self.background_filename)

            # load and scale the menu borders
            border = None
            if self.draw_borders:
                border = graphics.load_and_scale(self.borders_filename)

            # set the helper to draw the _background
            self.window = GraphicBox(border, background, self.background_color)

    def update_background(self, new_filename: str) -> None:
        self.background_filename = new_filename
        self.load_graphics()

    def show_cursor(self) -> None:
        """Show the cursor that indicates the selected object."""
        self.cursor_controller.show_cursor()

    def hide_cursor(self) -> None:
        """Hide the cursor that indicates the selected object."""
        self.cursor_controller.hide_cursor()

    def refresh_layout(self) -> None:
        """Fit border to contents and hide/show cursor."""
        self.menu_items.expand = not self.shrink_to_items

        # check if we have items, but they are all disabled
        disabled = all(not i.enabled for i in self.menu_items)

        if self.menu_items and not disabled:
            self.cursor_controller.show_cursor()
        else:
            self.cursor_controller.hide_cursor()

        if self.shrink_to_items:
            self.fit_border()

    def draw(self, surface: Surface) -> None:
        """
        Draws the menu object to a pygame surface.

        Parameters:
            surface: Surface to draw on.
        """
        if self._needs_refresh:
            self.refresh_layout()
            self._needs_refresh = False

        if not self.transparent:
            self.window.draw(surface, self.rect)

        if self._show_contents:
            self.menu_items.draw(surface)
            self.menu_sprites.draw(surface)

        self.sprites.draw(surface)

    def set_font(
        self,
        size: int = prepare.FONT_SIZE,
        font: Optional[str] = None,
        line_spacing: int = 10,
    ) -> Font:
        """
        Set the font properties that the menu uses.

        The size and line_spacing parameters will be adjusted the
        screen scale.  You should pass the original, unscaled values.

        Parameters:
            size: The font size in pixels.
            font: Path to the typeface file (.ttf).
            line_spacing: The spacing in pixels between lines of text.

        .. image:: images/menu/set_font.png
        """
        if font is None:
            font = self.font_filename

        if size < self.min_font_size:
            size = self.min_font_size

        self.line_spacing = tools.scale(line_spacing)

        if prepare.CONFIG.large_gui:
            self.font_size = tools.scale(size + 1)
        else:
            self.font_size = tools.scale(size)

        self.font = Font(font, self.font_size)
        return self.font

    def calc_internal_rect(self) -> Rect:
        """
        Calculate the area inside the borders, if any.

        If no borders are present, a copy of the menu rect will be returned.

        Returns:
            Rect representing space inside borders, if any.
        """
        return self.window.calc_inner_rect(self.rect)

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        """
        Delegates player input event handling to the MenuInputHandler.

        Parameters:
            event: A player input event, such as a key press or mouse click.

        Returns:
            The result of the event handling, which is either the original event
            if it was not handled, or None if the event was handled exclusively
            by the MenuInputHandler.
        """
        return self._input_handler.handle_event(event)

    def change_selection(self, index: int, animate: bool = True) -> None:
        """
        Force the menu to be evaluated.

        Move also cursor and trigger focus changes.
        """
        previous = self.get_selected_item()
        self.selected_index = index
        self.menu_select_sound.play()
        selected = self.get_selected_item()
        self.cursor_controller.update_selection_focus(previous, selected)
        self.on_menu_selection_change()

    def search_items(self, target_object: Any) -> Optional[MenuItem[T]]:
        """
        Non-optimised search through menu_items for a particular thing.

        Parameters:
            target_object: Object to search in the menu.

        Returns:
            Menu item containing the object, if found. Otherwise, None.
        """
        return next(
            (
                menu_item
                for menu_item in self.menu_items
                if menu_item.game_object == target_object
            ),
            None,
        )

    def get_selected_item(self) -> Optional[MenuItem[T]]:
        """
        Get the Menu Item that is currently selected.

        Returns:
            Selected menu item. if any.
        """
        try:
            return self.menu_items[self.selected_index]
        except IndexError:
            return None

    def resume(self) -> None:
        if self.state_controller.is_closed():

            def show_items() -> None:
                self.state_controller.set_normal()
                self._show_contents = True
                self.on_menu_selection_change()
                self.on_open()

            self.state_controller.open()
            self.reload_items()
            self.refresh_layout()

            ani = self.animate_open()
            if ani:
                if self.animate_contents:
                    self._show_contents = True
                    # TODO: make some "dirty" or invalidate layout API
                    # this will make sure items are arranged as menu opens
                    ani.schedule(
                        partial(
                            setattr,
                            self.menu_items,
                            "_needs_arrange",
                            True,
                        ),
                        ScheduleType.ON_UPDATE,
                    )
                ani.schedule(show_items, ScheduleType.ON_FINISH)
            else:
                self.state_controller.set_normal()
                show_items()

    def close(self) -> None:
        if self.state_controller.is_interactive():
            self.state_controller.close()
            ani = self.animate_close()
            self.on_close()
            if ani:
                ani.schedule(self.client.pop_state, ScheduleType.ON_FINISH)
            else:
                self.client.pop_state()

    def anchor(
        self, attribute: str, value: Union[int, tuple[int, int]]
    ) -> None:
        """
        Set an anchor for the menu window.

        You can pass any string value that is used in a pygame rect,
        for example: "center", "topleft", and "right".

        When changes are made to the window or it is being opened
        or sized, then these values passed as anchors will override
        others.  The order of which each anchor is applied is not
        necessarily going to match the order they were set, as the
        implementation relies on a dictionary.

        Take care to make sure values do not overlap.

        Parameters:
            attribute: Rect attribute to specify.
            value: Value of the attribute.
        """
        if value is None:
            del self._anchors[attribute]
        else:
            self._anchors[attribute] = value

    def position_rect(self) -> None:
        """Reposition rect taking in account the anchors"""
        for attribute, value in self._anchors.items():
            setattr(self.rect, attribute, value)

    # ============================================================================
    #   The following methods are designed to be monkey patched or overloaded
    # ============================================================================

    def calc_menu_items_rect(self) -> Rect:
        """
        Calculate the area inside the internal rect where items are listed.

        Returns:
            Rectangle that contains the menu items.
        """
        cursor_margin = self.cursor_controller.get_margin()
        inner = self.calc_internal_rect()
        menu_rect = inner.inflate(*cursor_margin)
        menu_rect.bottomright = inner.bottomright
        return menu_rect

    def calc_final_rect(self) -> Rect:
        """
        Calculate the area in the game window where menu is shown.

        This value is the __desired__ location and size, and should not change
        over the lifetime of the menu.  It is used to generate animations
        to open the menu.

        The rect represents the size of the menu after all items are added.

        Returns:
            Rectangle with the size of the menu.
        """
        original = self.rect.copy()  # store the original rect
        self.refresh_layout()  # arrange the menu
        rect = self.rect.copy()  # store the final rect
        self.rect = original  # set the original back
        return rect

    def on_open(self) -> None:
        """Hook is called after opening animation has finished."""

    def on_close(self) -> None:
        """Hook is called after opening animation has finished."""
        if self.on_close_callback:
            self.on_close_callback()

    def on_menu_selection(self, selected_item: MenuItem[T]) -> None:
        """
        Hook for things to happen when player selects a menu option.

        Parameters:
            selected_item: The selected menu item.

        Override in subclass, if you want to.
        """
        if selected_item.enabled:
            if selected_item.game_object is None:
                raise ValueError("Selected menu item has no game object")
            if not callable(selected_item.game_object):
                raise ValueError(
                    "Selected menu item's game object is not callable"
                )
            selected_item.game_object()

    def on_menu_selection_change(self) -> None:
        """
        Hook for things to happen after menu selection changes.

        Override in subclass.
        """
        if self.on_menu_selection_change_callback:
            self.on_menu_selection_change_callback()

    def animate_open(self) -> Optional[Animation]:
        """
        Called when menu is going to open.

        Menu will not receive input during the animation.
        Menu will only play this animation once.

        Must return either an Animation or Task to attach callback.
        Only modify state of the menu Rect.
        Do not change important state attributes.

        Returns:
            Open animation, if any.
        """
        return None

    def animate_close(self) -> Optional[Animation]:
        """
        Called when menu is going to open.

        Menu will not receive input during the animation.
        Menu will play animation only once.
        Menu will be popped after animation finished.

        Must return either an Animation or Task to attach callback.
        Only modify state of the menu Rect.
        Do not change important state attributes.

        Returns:
            Close animation, if any.
        """
        return None


class PopUpMenu(Menu[T]):
    """Menu with "pop up" style animation."""

    name: ClassVar[str] = "PopUpMenu"
    ANIMATION_DURATION = 0.20

    def __init__(self, initial_scale: float = 0.1, **kwargs: Any):
        super().__init__(**kwargs)
        self.initial_scale = initial_scale

    def _calculate_initial_rect(self, final_rect: Rect) -> Rect:
        """
        Calculates the initial rectangle for the animation.
        """
        initial_rect = final_rect.copy()
        initial_rect.width = int(final_rect.width * self.initial_scale)
        initial_rect.height = int(final_rect.height * self.initial_scale)
        initial_rect.center = final_rect.center
        return initial_rect

    def animate_open(self) -> Animation:
        # anchor the center of the popup
        final_rect = self.calc_final_rect()
        self.anchor("center", prepare.SCREEN_RECT.center)

        # set rect to a small size for the initial values of the animation
        self.rect = self._calculate_initial_rect(final_rect)

        # if this statement were removed, then the menu would
        # refresh and the size animation would be lost
        self._needs_refresh = False

        # create animation to open window with
        ani = self.animate(
            self.rect,
            height=final_rect.height,
            width=final_rect.width,
            duration=self.ANIMATION_DURATION,
        )
        ani.schedule(
            lambda: setattr(self.rect, "center", final_rect.center),
            ScheduleType.ON_UPDATE,
        )
        return ani


class InputHandler(ABC):
    @abstractmethod
    def handle_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        pass


class MenuInputHandler(InputHandler):
    """
    Handles input events for a Menu instance.
    """

    def __init__(self, menu: Menu[T]) -> None:
        self._menu = menu

    def handle_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        """
        Processes a single player input event.

        This function is only called when the player provides input such
        as pressing a key or clicking the mouse.

        Since this is part of a chain of event handlers, the return value
        from this method becomes input for the next one. Returning None
        signifies that this method has dealt with an event and wants it
        exclusively. Return the event and others can use it as well.

        You should return None if you have handled input here.

        Returns:
            Passed input if not handled here. ``None`` otherwise.
        """
        if self._handle_escape_key(event):
            return None
        if self._handle_selection_confirm(event):
            return None
        if self._handle_cursor_movement(event):
            return None
        if self._handle_mouse_selection(event):
            return None
        return event

    def _handle_escape_key(self, event: PlayerInput) -> bool:
        """Handles events related to closing the menu."""
        if event.button in (buttons.B, buttons.BACK, intentions.MENU_CANCEL):
            if event.pressed and self._menu.escape_key_exits:
                self._menu.close()
            return True
        return False

    def _get_valid_change_condition(self, event: PlayerInput) -> bool:
        """Determines if a menu change is currently valid."""
        menu_items = self._menu.menu_items
        disabled = all(not i.enabled for i in menu_items)
        return (
            event.pressed
            and self._menu.state_controller.is_enabled()
            and not disabled
            and len(menu_items) > 0
        )

    def _handle_selection_confirm(self, event: PlayerInput) -> bool:
        """Handles events related to confirming a menu selection."""
        if event.button in (buttons.A, intentions.SELECT):
            if self._get_valid_change_condition(event):
                self._menu.menu_select_sound.play()
                selected = self._menu.get_selected_item()
                if selected:
                    self._menu.on_menu_selection(selected)
            return True
        return False

    def _handle_cursor_movement(self, event: PlayerInput) -> bool:
        """Handles events related to moving the menu cursor."""
        if event.button in (
            buttons.UP,
            buttons.DOWN,
            buttons.LEFT,
            buttons.RIGHT,
        ):
            if self._get_valid_change_condition(event):
                index = self._menu.menu_items.determine_cursor_movement(
                    self._menu.selected_index,
                    event,
                )
                if self._menu.selected_index != index:
                    self._menu.change_selection(index)
            return True
        return False

    def _handle_mouse_selection(self, event: PlayerInput) -> bool:
        """
        Handles events related to mouse/touch selection of menu items.

        TODOs:
        - Handle click/drag interactions
        - Add support for screen scaling
        - Consider generalizing into a widget system

        Parameters:
            event: A PlayerInput event corresponding to MOUSELEFT.

        Returns:
            True if the event was handled, False otherwise.
        """
        if event.button == buttons.MOUSELEFT:
            if self._menu.touch_aware and self._get_valid_change_condition(
                event
            ):
                mouse_pos = event.value
                if (
                    not isinstance(mouse_pos, (list, tuple))
                    or len(mouse_pos) != 2
                ):
                    raise ValueError(
                        f"Invalid mouse_pos received: {mouse_pos}"
                    )
                if mouse_pos is None:
                    logger.warning(
                        f"Received unexpected mouse_pos value: {mouse_pos}"
                    )
                    return True  # Still consume the event, but log a warning

                if hasattr(self._menu.menu_items, "update_rect_from_parent"):
                    self._menu.menu_items.update_rect_from_parent()
                else:
                    logger.debug(
                        "menu_items does not implement update_rect_from_parent"
                    )
                    return True  # Gracefully skip processing, but log a debug message

                # Adjust mouse position relative to menu_items group
                mouse_pos = [
                    a - b
                    for a, b in zip(
                        mouse_pos,
                        self._menu.menu_items.rect.topleft,
                    )
                ]

                if not self._menu.menu_items.rect.collidepoint(mouse_pos):
                    logger.debug(
                        "Mouse click was outside the bounds of menu items."
                    )
                    return True

                for index, item in enumerate(
                    [i for i in self._menu.menu_items if i.enabled]
                ):
                    if item.rect.collidepoint(mouse_pos):
                        self._menu.change_selection(index)
                        selected = self._menu.get_selected_item()
                        if selected:
                            self._menu.on_menu_selection(selected)
                        else:
                            raise RuntimeError(
                                "Menu selection was None despite enabled item being clicked"
                            )
                        return True
            return True  # Mouse click occurred but not processed
        return False
