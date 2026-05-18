# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import tempfile
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from functools import partial
from typing import TYPE_CHECKING, Any, ClassVar, Generic, TypedDict, TypeVar

from pygame import SRCALPHA, image
from pygame.font import Font
from pygame.rect import Rect
from pygame.surface import Surface
from pygame_menu.baseimage import BaseImage
from pygame_menu.locals import (
    ALIGN_LEFT,
    POSITION_CENTER,
    SCROLLAREA_POSITION_NONE,
)
from pygame_menu.menu import Menu as PyMenu
from pygame_menu.sound import Sound
from pygame_menu.themes import Theme
from pygame_menu.widgets.core.widget import Widget

from tuxemon.animation import Animation, ScheduleType
from tuxemon.constants.asset_loader import fetch_asset
from tuxemon.graphics import ColorLike, load_and_scale, load_image
from tuxemon.menu.controller import MenuController
from tuxemon.menu.cursor import MenuCursor, MenuCursorController
from tuxemon.menu.input_handler import (
    MenuInputHandler,
    PygameMenuInputHandler,
)
from tuxemon.menu.interface import MenuItem
from tuxemon.menu.theme import get_sound_engine, get_theme
from tuxemon.platform.const.graphics import (
    BACKGROUND_COLOR,
    FONT_COLOR,
    FONT_SHADOW_COLOR,
    FONT_SIZE,
    FONT_SIZE_BIG,
    FONT_SIZE_BIGGER,
    FONT_SIZE_BIGGEST,
    FONT_SIZE_SMALL,
    FONT_SIZE_SMALLER,
    UNAVAILABLE_COLOR,
    UNAVAILABLE_COLOR_SHOP,
)
from tuxemon.sprite import (
    RelativeGroup,
    SpriteGroup,
    VisualSpriteList,
)
from tuxemon.state.state import State
from tuxemon.tools import transform_resource_filename
from tuxemon.ui.graphic_box import GraphicBox
from tuxemon.ui.text_renderer import TextRenderer
from tuxemon.user_config import CONFIG

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.menu.alert import AlertManager
    from tuxemon.platform.events import PlayerInput
    from tuxemon.prepare import DisplayContext

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FontSettings:
    smaller: int
    small: int
    medium: int
    big: int
    bigger: int
    biggest: int

    @classmethod
    def from_context(cls, context: DisplayContext) -> FontSettings:
        s = context.scaling.scale_int
        return cls(
            smaller=s(FONT_SIZE_SMALLER),
            small=s(FONT_SIZE_SMALL),
            medium=s(FONT_SIZE),
            big=s(FONT_SIZE_BIG),
            bigger=s(FONT_SIZE_BIGGER),
            biggest=s(FONT_SIZE_BIGGEST),
        )


T = TypeVar("T", covariant=True)


class MenuConfig(TypedDict):
    width: int
    height: int
    theme: Theme | None
    sound_engine: Sound | None
    menu_kwargs: dict[str, Any]
    columns: int | None
    rows: int | None


class PygameMenuState(State):
    name: ClassVar[str] = "PygameMenuState"
    transparent = True

    def __init__(
        self,
        client: BaseClient,
        *,
        width: int = 1,
        height: int = 1,
        theme: Theme | None = None,
        sound_engine: Sound | None = None,
        font_settings: FontSettings | None = None,
        menu_kwargs: dict[str, Any] | None = None,
        **state_kwargs: Any,
    ) -> None:
        super().__init__(client=client, **state_kwargs)

        self.font_settings = font_settings
        self.font_type = font_settings or FontSettings.from_context(
            client.context
        )

        self._menu_config = {
            "width": width,
            "height": height,
            "theme": theme,
            "sound_engine": sound_engine,
            "menu_kwargs": menu_kwargs or {},
            "columns": state_kwargs.pop("columns", None),
            "rows": state_kwargs.pop("rows", None),
        }

        self.state_controller = MenuController()
        self.open = False
        self.escape_key_exits = True
        self.selected_widget: Widget | None = None
        self._input_handler = PygameMenuInputHandler(self)
        self._menu: PyMenu | None = None

    @property
    def menu(self) -> PyMenu:
        """
        Public, non-optional menu.
        Lazily builds the menu if needed.
        """
        if self._menu is None:
            self.setup()
        assert self._menu is not None
        return self._menu

    def setup(self) -> None:
        """
        Build or rebuild the menu.
        Idempotent: safe to call multiple times.
        """
        cfg = self._menu_config

        base_theme = cfg["theme"] or get_theme(self.client.context.scaling)
        theme = self._copy_theme(base_theme)

        columns = cfg["columns"]
        rows = cfg["rows"]

        kwargs = {
            "theme": theme,
            "center_content": True,
            "onclose": self._on_close,
            **cfg["menu_kwargs"],
        }

        if columns is not None:
            kwargs["columns"] = columns
        if rows is not None:
            kwargs["rows"] = rows

        menu = PyMenu(
            "",
            cfg["width"],
            cfg["height"],
            **kwargs,
        )

        sound_engine = cfg["sound_engine"]
        if sound_engine is None:
            sound_file = self.client.sound_manager.get_sound_filename(
                self.client.config.menu_sound
            )
            sound_volume = self.client.config.sound_volume
            sound_engine = get_sound_engine(sound_volume, sound_file)

        menu.set_sound(sound_engine)
        # If we 'ignore nonphysical keyboard', pygame_menu will check the
        # pygame event queue to make sure there is an actual keyboard event
        # being pressed right now, and ignore the event if not, hence it won't
        # work for controllers.
        menu._keyboard_ignore_nonphysical = False

        self._menu = menu

    def _copy_theme(self, theme: Theme) -> Theme:
        """
        pygame_menu.Theme.copy() is shallow, so we deep-copy only the fields
        that are known to cause cross-menu bleed.
        """
        new = theme.copy()

        if hasattr(theme, "widget_font"):
            new.widget_font = theme.widget_font

        if hasattr(theme, "title_font"):
            new.title_font = theme.title_font

        return new

    def _create_image(
        self, path: str, position: str = POSITION_CENTER
    ) -> BaseImage:
        return BaseImage(
            image_path=transform_resource_filename(path),
            drawing_position=position,
        )

    def _create_image_from_surface(
        self, surface: Surface, position: str = POSITION_CENTER
    ) -> BaseImage:
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        tmp_path = tmp.name
        tmp.close()

        image.save(surface, tmp_path)

        return BaseImage(
            image_path=tmp_path,
            load_from_file=True,
            drawing_position=position,
        )

    def _setup_theme(
        self, background: str, position: str = POSITION_CENTER
    ) -> Theme:
        theme = self._copy_theme(get_theme(self.client.context.scaling))
        theme.background_color = self._create_image(background, position)
        return theme

    def resume(self) -> None:
        """
        Called when the state becomes active.
        Ensures menu exists, then opens it.
        """
        _ = self.menu
        self.refresh()

        if self.state_controller.is_closed():
            self.state_controller.open()
            animation = self.animate_open()
            if animation:
                animation.schedule(self._set_open, ScheduleType.ON_FINISH)
            else:
                self._set_open()

        super().resume()

    def refresh(self) -> None:
        """Subclasses override to update widget data."""

    def _set_open(self) -> None:
        self.open = True
        self.state_controller.set_normal()
        self.menu.enable()

    def process_event(self, event: PlayerInput) -> PlayerInput | None:
        return self._input_handler.handle_event(event)

    def valid_press(self, event: PlayerInput) -> bool:
        return self._input_handler._is_press(event, 0.5)

    def update_selected_widget(self) -> None:
        self.selected_widget = self.menu.get_selected_widget()

    def draw(self, surface: Surface) -> None:
        if not self.state_controller.is_closed() and self.menu.is_enabled():
            self.menu.draw(surface)

    def disable(self) -> None:
        if self.state_controller.is_enabled():
            self.state_controller.disable()
            self.menu.disable()

    def enable(self) -> None:
        if self.state_controller.is_disabled():
            self.state_controller.set_normal()
            self.menu.enable()

    def _on_close(self) -> None:
        self.open = False
        self.state_controller.close()
        self.selected_widget = None

        animation = self.animate_close()
        if animation:
            animation.schedule(self.client.pop_state, ScheduleType.ON_FINISH)
        else:
            self.client.pop_state()

    def _finalize(self) -> None:
        if self._menu is not None:
            self._menu.disable()
            self._menu.clear()
        self.selected_widget = None
        self.open = False

    def reset_theme(self) -> None:
        """
        Reset the menu's theme, not the global theme.
        """
        if self._menu is None:
            return

        theme = self._copy_theme(get_theme(self.client.context.scaling))
        theme.scrollarea_position = SCROLLAREA_POSITION_NONE
        theme.background_color = BACKGROUND_COLOR
        theme.widget_alignment = ALIGN_LEFT
        theme.title = False

        self._menu._theme = theme

    def animate_open(self) -> Animation | None:
        return None

    def animate_close(self) -> Animation | None:
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
    background_color: ColorLike = BACKGROUND_COLOR
    font_color: ColorLike = FONT_COLOR
    font_shadow_color: ColorLike = FONT_SHADOW_COLOR
    # Font color when the action is unavailable
    unavailable_color: ColorLike = UNAVAILABLE_COLOR
    unavailable_color_shop: ColorLike = UNAVAILABLE_COLOR_SHOP
    # File to load for image background
    background_filename: str | None = None
    menu_select_sound_filename = CONFIG.menu_sound
    font_filename = CONFIG.locale.font_file
    borders_filename = CONFIG.menu_border
    cursor_filename = CONFIG.menu_cursor
    cursor_move_duration = 0.20
    shrink_to_items = False  # fit the border to contents
    escape_key_exits = True  # escape key closes menu
    animate_contents = False  # show contents while window opens
    # if true, then menu items can be selected with the mouse/touch
    touch_aware = True

    def __init__(
        self, client: BaseClient, selected_index: int = 0, **kwargs: Any
    ) -> None:
        super().__init__(client=client, **kwargs)

        self.rect = self.rect.copy()  # do not remove!
        self.selected_index = selected_index
        # state: closed, opening, normal, disabled, closing
        self.state_controller = MenuController()
        self._show_contents: bool = False
        self._needs_refresh: bool = False
        self._layout_passes: int = 0
        self._anchors: list[tuple[str, int | tuple[int, int]]] = []
        self.__dict__.update(kwargs)

        # holds sprites representing menu items
        self.create_new_menu_items_group()

        # callbacks
        self.on_close_callback: Callable[[], None] | None = None
        self.on_menu_selection_change_callback: Callable[[], None] | None = (
            None
        )

        self.font_filename = fetch_asset("font", self.font_filename)
        self.font = self.set_font()  # load default font
        self.load_graphics()  # load default graphics
        self.reload_sounds()  # load default sounds
        self._input_handler = MenuInputHandler(self)
        self._text_renderer = TextRenderer(
            scaling=self.client.context.scaling,
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
            context=self.client.context,
            remove_animations=self.remove_animations_of,
        )

    @property
    def dialog(self) -> AlertManager:
        return self.client.alert_manager

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

    def invalidate_layout(self, reason: str = "") -> None:
        self._needs_refresh = True
        logger.debug(reason)

    def validate_layout(self, reason: str = "") -> None:
        self._needs_refresh = False
        logger.debug(reason)

    def initialize_items(self) -> Iterable[MenuItem[T]] | None:
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
        self.invalidate_layout("items changed")
        items = self.initialize_items()

        if items is None:
            # No change requested
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
        icon: Surface | None = None,
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
        self.invalidate_layout("item added")

    def clear(self) -> None:
        """Clears all menu items."""
        self.menu_items.clear_items()
        self.invalidate_layout("items cleared")

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
        rect1.width += self.client.context.scaling.scale_int(18)
        rect1.height += self.client.context.scaling.scale_int(19)
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
        fg: ColorLike | None = None,
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
                background = load_image(self.background_filename)

            # load and scale the menu borders
            if self.draw_borders:
                border = load_and_scale(self.borders_filename)
            else:
                border = Surface((1, 1), SRCALPHA)

            # set the helper to draw the background
            self.window = GraphicBox(
                self.rect.copy(),
                border,
                background=background,
                color=self.background_color,
            )

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
        self._layout_passes += 1
        logger.debug(
            f"[{self.name}] layout pass #{self._layout_passes} (needs_refresh={self._needs_refresh})"
        )
        self.arrange_items()
        self.update_cursor_visibility()
        self.update_border()

    def arrange_items(self) -> None:
        self.menu_items.expand = not self.shrink_to_items
        self.menu_items.arrange_menu_items()

    def update_cursor_visibility(self) -> None:
        disabled = all(not i.enabled for i in self.menu_items)
        if self.menu_items and not disabled:
            self.cursor_controller.show_cursor()
        else:
            self.cursor_controller.hide_cursor()

    def update_border(self) -> None:
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
            self.validate_layout("refresh layout")

        if not self.transparent:
            self.window.draw(surface, self.rect)

        if self._show_contents:
            self.menu_items.draw(surface)
            self.menu_sprites.draw(surface)

        self.sprites.draw(surface)

    def set_transparent(self, is_transparent: bool) -> None:
        """Sets the menu's transparency state."""
        self.transparent = is_transparent

        if not self.transparent:
            self.load_graphics()

    def set_font(
        self,
        size: int = FONT_SIZE,
        font: str | None = None,
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

        self.line_spacing = self.client.context.scaling.scale_int(line_spacing)

        if self.client.config.large_gui:
            self.font_size = self.client.context.scaling.scale_int(size + 1)
        else:
            self.font_size = self.client.context.scaling.scale_int(size)

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

    def valid_press(self, event: PlayerInput) -> bool:
        return self._input_handler._valid_press(event)

    def process_event(self, event: PlayerInput) -> PlayerInput | None:
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

    def set_selected_index(self, index: int) -> None:
        self.selected_index = index

    def change_selection(self, index: int, animate: bool = True) -> None:
        """
        Force the menu to be evaluated.

        Move also cursor and trigger focus changes.
        """
        previous = self.get_selected_item()
        self.set_selected_index(index)
        self.menu_select_sound.play()
        selected = self.get_selected_item()
        self.cursor_controller.update_selection_focus(
            previous, selected, animate
        )
        self.on_menu_selection_change()

    def search_items(self, target_object: Any) -> MenuItem[T] | None:
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

    def get_selected_item(self) -> MenuItem[T] | None:
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

    def anchor(self, attribute: str, value: int | tuple[int, int]) -> None:
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
        self._anchors = [(a, v) for (a, v) in self._anchors if a != attribute]
        if value is not None:
            self._anchors.append((attribute, value))

    def position_rect(self) -> None:
        """Reposition rect taking in account the anchors"""
        for attribute, value in self._anchors:
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

    def animate_open(self) -> Animation | None:
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

    def animate_close(self) -> Animation | None:
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

    def __init__(
        self, client: BaseClient, initial_scale: float = 0.1, **kwargs: Any
    ):
        super().__init__(client=client, **kwargs)
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
        self.anchor("center", self.client.context.rect.center)

        # set rect to a small size for the initial values of the animation
        self.rect = self._calculate_initial_rect(final_rect)

        # if this statement were removed, then the menu would
        # refresh and the size animation would be lost
        self.validate_layout("animate_open")

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
