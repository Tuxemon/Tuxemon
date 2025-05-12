# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import math
from collections.abc import Callable, Iterable, Sequence
from enum import Enum
from functools import partial
from typing import Any, Generic, Optional, TypeVar, Union

import pygame_menu
from pygame import SRCALPHA
from pygame.font import Font
from pygame.rect import Rect
from pygame.surface import Surface
from pygame_menu import baseimage, locals, themes
from pygame_menu.widgets.core.widget import Widget

from tuxemon import graphics, prepare, tools
from tuxemon.animation import Animation
from tuxemon.graphics import ColorLike
from tuxemon.menu.events import playerinput_to_event
from tuxemon.menu.interface import MenuCursor, MenuItem
from tuxemon.menu.theme import get_sound_engine, get_theme
from tuxemon.platform.const import buttons, intentions
from tuxemon.platform.events import PlayerInput
from tuxemon.prepare import CONFIG
from tuxemon.sprite import (
    RelativeGroup,
    SpriteGroup,
    VisualSpriteList,
)
from tuxemon.state import State
from tuxemon.ui.draw import GraphicBox
from tuxemon.ui.text import TextArea

logger = logging.getLogger(__name__)


class MenuState(Enum):
    CLOSED = "closed"
    OPENING = "opening"
    NORMAL = "normal"
    DISABLED = "disabled"
    CLOSING = "closing"


def layout_func(scale: float) -> Callable[[Sequence[float]], Sequence[float]]:
    def func(area: Sequence[float]) -> Sequence[float]:
        return [scale * i for i in area]

    return func


layout = layout_func(prepare.SCALE)

T = TypeVar("T", covariant=True)


class PygameMenuState(State):
    """
    A Pygame menu state class.
    """

    transparent = True

    # Colors
    background_color = prepare.BACKGROUND_COLOR
    font_color = prepare.FONT_COLOR
    font_shadow_color = prepare.FONT_SHADOW_COLOR
    scrollbar_color = prepare.SCROLLBAR_COLOR
    scrollbar_slider_color = prepare.SCROLLBAR_SLIDER_COLOR
    transparent_color = prepare.TRANSPARENT_COLOR

    # Font sizes
    font_size_smaller = tools.scale(prepare.FONT_SIZE_SMALLER)
    font_size_small = tools.scale(prepare.FONT_SIZE_SMALL)
    font_size = tools.scale(prepare.FONT_SIZE)
    font_size_big = tools.scale(prepare.FONT_SIZE_BIG)
    font_size_bigger = tools.scale(prepare.FONT_SIZE_BIGGER)

    def __init__(
        self,
        width: int = 1,
        height: int = 1,
        theme: Optional[pygame_menu.Theme] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__()
        if theme is None:
            theme = get_theme()

        self._initialize_attributes(theme)
        self._create_menu(width, height, theme, **kwargs)

    def _initialize_attributes(self, theme: pygame_menu.Theme) -> None:
        """
        Initializes the attributes of the menu state.

        Parameters:
            theme: The theme of the menu.
        """
        self.open = False
        self.escape_key_exits = True
        self.selected_widget: Optional[Widget] = None

        # Fonts
        theme.widget_font_size = self.font_size
        theme.title_font_size = self.font_size_big

        # Colors
        theme.widget_font_color = self.font_color
        theme.selection_color = self.font_color
        theme.scrollbar_color = self.scrollbar_color
        theme.scrollbar_slider_color = self.scrollbar_slider_color
        theme.title_font_color = self.font_color
        theme.title_background_color = self.transparent_color
        theme.widget_font_shadow_color = self.font_shadow_color
        font = prepare.fetch("font", prepare.CONFIG.locale.font_file)
        theme.title_font = font
        theme.widget_font = font

    def _create_menu(
        self, width: int, height: int, theme: pygame_menu.Theme, **kwargs: Any
    ) -> None:
        """
        Creates the Pygame menu.

        Parameters:
            width: The width of the menu.
            height: The height of the menu.
            theme: The theme of the menu.
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
        sound_file = self.client.sound_manager.get_sound_filename(
            "sound_menu_select"
        )
        sound_volume = self.client.config.sound_volume
        self.menu.set_sound(get_sound_engine(sound_volume, sound_file))
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
            event.button in {buttons.B, buttons.BACK, intentions.MENU_CANCEL}
            and not self.escape_key_exits
        ):
            return None

        try:
            pygame_event = playerinput_to_event(event)
            if (
                self.open is True
                and event.pressed
                and pygame_event is not None
            ):
                self.menu.update([pygame_event])
                # Get the currently selected widget
                self.selected_widget = self.menu.get_selected_widget()
        except Exception as e:
            # Handle the exception
            pass

        return event if pygame_event is None else None

    def draw(self, surface: Surface) -> None:
        """
        Draws the menu on the given surface.

        Parameters:
            surface: The surface to draw on.
        """
        self.menu.draw(surface)

    def _set_open(self) -> None:
        """
        Sets the menu as open.
        """
        self.open = True

    def resume(self) -> None:
        """
        Resumes the menu.
        """
        animation = self.animate_open()
        if animation:
            animation.callback = self._set_open
        else:
            self.open = True

    def _on_close(self) -> None:
        """
        Called when the menu is closed.
        """
        self.open = False
        self.reset_theme()
        self.menu.enable()
        animation = self.animate_close()
        if animation:
            animation.callback = self.client.pop_state
        else:
            self.client.pop_state()

    def reset_theme(self) -> None:
        """Reset to original theme (color, alignment, etc.)"""
        theme = get_theme()
        theme.scrollarea_position = locals.SCROLLAREA_POSITION_NONE
        theme.background_color = self.background_color
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
    menu_select_sound_filename = "sound_menu_select"
    font_filename = prepare.CONFIG.locale.font_file
    borders_filename = "gfx/borders/borders.png"
    cursor_filename = "gfx/arrow.png"
    cursor_move_duration = 0.20
    default_character_delay = 0.05
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
        self.state = MenuState.CLOSED
        self._show_contents = False
        self._needs_refresh = False
        self._anchors: dict[str, Union[int, tuple[int, int]]] = {}
        self.__dict__.update(kwargs)

        # holds sprites representing menu items
        self.create_new_menu_items_group()

        # callbacks
        self.on_close_callback: Optional[Callable[[], None]] = None
        self.on_menu_selection_change_callback: Optional[
            Callable[[], None]
        ] = None

        self.font_filename = prepare.fetch("font", self.font_filename)
        self.set_font()  # load default font
        self.load_graphics()  # load default graphics
        self.reload_sounds()  # load default sounds

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

        del self.arrow
        del self.menu_items
        del self.menu_sprites

    def start_text_animation(
        self,
        text_area: TextArea,
        callback: Optional[Callable[[], None]] = None,
    ) -> None:
        """
        Start an animation to show text area, one character at a time.

        Parameters:
            text_area: Text area to animate.
            callback: Function called when alert is complete.

        """

        def next_character() -> None:
            try:
                next(text_area)
            except StopIteration:
                if callback:
                    callback()
            else:
                self.task(next_character, self.character_delay)

        self.character_delay = self.default_character_delay
        next_character()

    def animate_text(
        self,
        text_area: TextArea,
        text: str,
        callback: Optional[Callable[[], None]] = None,
        dialog_speed: str = "slow",
    ) -> None:
        """
        Set and animate a text area.

        Parameters:
            text_area: Text area to animate.
            text: Text to display.
            callback: Function called when alert is complete.
            dialog_speed: Speed of blitting chars to the dialog box.
        """
        text_area.text = text
        if CONFIG.dialog_speed == "max" or dialog_speed == "max":
            # exhaust the iterator to immediately blit every char to the dialog
            # box
            for _ in text_area:
                pass
            if callback:
                callback()
        else:
            self.start_text_animation(text_area, callback)

    def alert(
        self,
        message: str,
        callback: Optional[Callable[[], None]] = None,
        dialog_speed: str = "slow",
    ) -> None:
        """
        Write a message to the first available text area.

        Generally, a state will have just one, if any, text area.
        The first one found will be used to display the message.
        If no text area is found, a RuntimeError will be raised.

        Parameters:
            message: Message to write.
            callback: Function called when alert is complete.
            dialog_speed: Speed of blitting chars to the dialog box.
        """

        def find_textarea() -> TextArea:
            for sprite in self.sprites:
                if isinstance(sprite, TextArea):
                    return sprite
            raise RuntimeError(
                "attempted to use 'alert' on state without a TextArea",
                message,
            )

        self.animate_text(find_textarea(), message, callback, dialog_speed)

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
        """
        Draw shadowed text.

        Parameters:
            text: Text to draw.
            bg: Font shadow color.
            fg: Font color.
            offset: Offset of the shadow from the text.
                Defaults to (0.5, 0.5).

        Returns:
            Surface with the drawn text.
        """
        if not fg:
            fg = self.font_color

        font_color = self.font.render(text, True, fg)
        shadow_color = self.font.render(text, True, bg)

        _offset = layout(offset)
        size = [
            int(math.ceil(a + b))
            for a, b in zip(_offset, font_color.get_size())
        ]
        image = Surface(size, SRCALPHA)

        image.blit(shadow_color, tuple(_offset))
        image.blit(font_color, (0, 0))
        return image

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

        # handle the arrow cursor
        image = graphics.load_and_scale(self.cursor_filename)
        self.arrow = MenuCursor(image)

    def update_background(self, new_filename: str) -> None:
        self.background_filename = new_filename
        self.load_graphics()

    def show_cursor(self) -> None:
        """Show the cursor that indicates the selected object."""
        if self.arrow not in self.menu_sprites:
            self.menu_sprites.add(self.arrow)
        self.trigger_cursor_update(False)
        selected = self.get_selected_item()
        assert selected
        selected.in_focus = True

    def hide_cursor(self) -> None:
        """Hide the cursor that indicates the selected object."""
        if self.arrow in self.menu_sprites:
            self.menu_sprites.remove(self.arrow)
            selected = self.get_selected_item()
            if selected is not None:
                selected.in_focus = False

    def refresh_layout(self) -> None:
        """Fit border to contents and hide/show cursor."""
        self.menu_items.expand = not self.shrink_to_items

        # check if we have items, but they are all disabled
        disabled = all(not i.enabled for i in self.menu_items)

        if self.menu_items and not disabled:
            self.show_cursor()
        else:
            self.hide_cursor()

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
        size: int = 5,
        font: Optional[str] = None,
        line_spacing: int = 10,
    ) -> None:
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
        Handles player input events.

        Parameters:
            event: A player input event, such as a key press or mouse click.

        This function is only called when the player provides input such
        as pressing a key or clicking the mouse.

        Since this is part of a chain of event handlers, the return value
        from this method becomes input for the next one.  Returning None
        signifies that this method has dealt with an event and wants it
        exclusively.  Return the event and others can use it as well.

        You should return None if you have handled input here.

        Returns:
            Passed input if not handled here. ``None`` otherwise.

        """
        handled_event = False

        # close menu
        if event.button in (buttons.B, buttons.BACK, intentions.MENU_CANCEL):
            handled_event = True
            if event.pressed and self.escape_key_exits:
                self.close()

        disabled = True
        if hasattr(self, "menu_items") and event.pressed:
            disabled = all(not i.enabled for i in self.menu_items)
        valid_change = (
            event.pressed
            and self.state == MenuState.NORMAL
            and not disabled
            and self.menu_items
        )

        # confirm selection
        if event.button in (buttons.A, intentions.SELECT):
            handled_event = True
            if valid_change:
                self.menu_select_sound.play()
                selected = self.get_selected_item()
                assert selected
                self.on_menu_selection(selected)

        # cursor movement
        if event.button in (
            buttons.UP,
            buttons.DOWN,
            buttons.LEFT,
            buttons.RIGHT,
        ):
            handled_event = True
            if valid_change:
                index = self.menu_items.determine_cursor_movement(
                    self.selected_index,
                    event,
                )
                if not self.selected_index == index:
                    self.change_selection(index)

        # mouse/touch selection
        if event.button in (buttons.MOUSELEFT,):
            handled_event = True
            # TODO: handling of click/drag, miss-click, etc
            # TODO: eventually, maybe move some handling into menuitems
            # TODO: handle screen scaling?
            # TODO: generalized widget system
            if self.touch_aware and valid_change:
                mouse_pos = event.value
                assert mouse_pos != 0

                try:
                    self.menu_items.update_rect_from_parent()
                except AttributeError:
                    pass
                else:
                    mouse_pos = [
                        a - b
                        for a, b in zip(
                            mouse_pos,
                            self.menu_items.rect.topleft,
                        )
                    ]

                for index, item in enumerate(
                    [i for i in self.menu_items if i.enabled]
                ):
                    if item.rect.collidepoint(mouse_pos):
                        self.change_selection(index)
                        selected = self.get_selected_item()
                        assert selected
                        self.on_menu_selection(selected)

        return event if not handled_event else None

    def change_selection(self, index: int, animate: bool = True) -> None:
        """
        Force the menu to be evaluated.

        Move also cursor and trigger focus changes.

        """
        previous = self.get_selected_item()
        if previous is not None:
            previous.in_focus = False
        self.selected_index = index
        self.menu_select_sound.play()
        self.trigger_cursor_update(animate)
        selected = self.get_selected_item()
        assert selected
        selected.in_focus = True
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

    def trigger_cursor_update(
        self, animate: bool = True
    ) -> Optional[Animation]:
        """
        Force the menu cursor to move into the correct position.

        Parameters:
            animate: If True, then arrow will move smoothly into position.

        Returns:
            Animation of the cursor if ``animate`` is ``True``. ``None``
            otherwise.

        """
        selected = self.get_selected_item()
        if not selected:
            return None

        x, y = selected.rect.midleft
        x -= tools.scale(2)

        if animate:
            self.remove_animations_of(self.arrow.rect)
            return self.animate(
                self.arrow.rect,
                right=x,
                centery=y,
                duration=self.cursor_move_duration,
            )
        else:
            self.arrow.rect.midright = x, y
            return None

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
        if self.state == MenuState.CLOSED:

            def show_items() -> None:
                self.state = MenuState.NORMAL
                self._show_contents = True
                self.on_menu_selection_change()
                self.on_open()

            self.state = MenuState.OPENING
            self.reload_items()
            self.refresh_layout()

            ani = self.animate_open()
            if ani:
                if self.animate_contents:
                    self._show_contents = True
                    # TODO: make some "dirty" or invalidate layout API
                    # this will make sure items are arranged as menu opens
                    ani.update_callback = partial(
                        setattr,
                        self.menu_items,
                        "_needs_arrange",
                        True,
                    )
                ani.callback = show_items
            else:
                self.state = MenuState.NORMAL
                show_items()

    def close(self) -> None:
        if self.state in [MenuState.NORMAL, MenuState.OPENING]:
            self.state = MenuState.CLOSING
            ani = self.animate_close()
            self.on_close()
            if ani:
                ani.callback = self.client.pop_state
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
        # WARNING: hardcoded values related to menu arrow size
        #          if menu arrow image changes, this should be adjusted
        cursor_margin = -tools.scale(11), -tools.scale(5)
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
        self.anchor("center", self.client.screen.get_rect().center)

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
        ani.update_callback = lambda: setattr(
            self.rect, "center", final_rect.center
        )
        return ani
