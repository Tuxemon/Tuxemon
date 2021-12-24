from __future__ import annotations
import logging
import math
from functools import partial

import pygame

from tuxemon import audio, prepare, state, tools, graphics
from tuxemon.menu.interface import MenuCursor, MenuItem
from tuxemon.platform.const import intentions
from tuxemon.platform.const import buttons
from tuxemon.sprite import RelativeGroup, VisualSpriteList, SpriteGroup,\
    MenuSpriteGroup
from tuxemon.ui.draw import GraphicBox
from tuxemon.ui.text import TextArea
from typing import Any, Callable, Optional, Literal, Dict, Sequence, Tuple,\
    Iterable, TypeVar, Generic
from tuxemon.graphics import ColorLike
from tuxemon.platform.events import PlayerInput
from tuxemon.animation import Animation

logger = logging.getLogger(__name__)

MenuState = Literal["closed", "opening", "normal", "disabled", "closing"]


def layout_func(scale: float) -> Callable[[Sequence[float]], Sequence[float]]:
    def func(area: Sequence[float]) -> Sequence[float]:
        return [scale * i for i in area]

    return func


layout = layout_func(prepare.SCALE)

T = TypeVar("T", covariant=True)


class Menu(Generic[T], state.State):
    """
    A class to create menu objects.

    Menus are a type of game state.  Menus that are the top state
    will receive player input and respond to it.  They may be
    stacked, so that menus are nested.

    Attributes:
        rect: The rect of the menu in pixels, defaults to 0, 0, 400, 200.
        state: An arbitrary state of the menu. E.g. "opening" or "closing".
        selected_index: The index position of the currently selected menu item.
        menu_items: A list of available menu items.

    """

    # defaults for the menu
    columns = 1
    min_font_size = 4
    draw_borders = True
    background = None  # Image used to draw the background
    background_color: ColorLike = (248, 248, 248)  # The window's background color
    unavailable_color: ColorLike = (220, 220, 220)  # Font color when the action is unavailable
    background_filename: Optional[str] = None  # File to load for image background
    menu_select_sound_filename = "sound_menu_select"
    font_filename = "PressStart2P.ttf"
    borders_filename = "gfx/dialog-borders01.png"
    cursor_filename = "gfx/arrow.png"
    cursor_move_duration = 0.20
    default_character_delay = 0.05
    shrink_to_items = False  # fit the border to contents
    escape_key_exits = True  # escape key closes menu
    animate_contents = False  # show contents while window opens
    touch_aware = True  # if true, then menu items can be selected with the mouse/touch

    def startup(self, *, selected_index: int = 0, **kwargs: Any) -> None:
        self.rect = self.rect.copy()  # do not remove!
        self.selected_index = selected_index  # track which menu item is selected
        self.state: MenuState = "closed"  # closed, opening, normal, disabled, closing
        self._show_contents = False  # draw menu items, or not
        self._needs_refresh = False  # refresh layout on next draw
        self._anchors: Dict[str, Tuple[int, int]] = {}  # used to position the menu/state
        self.__dict__.update(kwargs)  # may be removed in the future

        # holds sprites representing menu items
        self.create_new_menu_items_group()

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
        self.menu_items: MenuSpriteGroup[MenuItem[T]] = VisualSpriteList(
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

        self.client.release_controls()

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
        self.remove_animations_of(next_character)
        next_character()

    def animate_text(
        self,
        text_area: TextArea,
        text: str,
        callback: Optional[Callable[[], None]] = None,
    ) -> None:
        """
        Set and animate a text area.

        Parameters:
            text_area: Text area to animate.
            text: Text to display.
            callback: Function called when alert is complete.

        """
        text_area.text = text
        self.start_text_animation(text_area, callback)

    def alert(
        self,
        message: str,
        callback: Optional[Callable[[], None]] = None,
    ) -> None:
        """
        Write a message to the first available text area.

        Generally, a state will have just one, if any, text area.
        The first one found will be use to display the message.
        If no text area is found, a RuntimeError will be raised.

        Parameters:
            message: Message to write.
            callback: Function called when alert is complete.

        """

        def find_textarea() -> TextArea:
            for sprite in self.sprites:
                if isinstance(sprite, TextArea):
                    return sprite
            logger.error(
                "attempted to use 'alert' on state without a TextArea",
                message,
            )
            raise RuntimeError

        self.animate_text(find_textarea(), message, callback)

    def initialize_items(self) -> Optional[Iterable[MenuItem[T]]]:
        """
        Advanced way to fill in menu items.

        For menus that change dynamically, use of this method will
        make changes to the menu easier.

        """

    def is_valid_entry(self, game_object: Any) -> bool:
        """
        Checked when items are loaded/reloaded.

        The return value will enable/disable menu items

        WIP.  The value passed should be Item.game_object.

        Parameters:
            game_object: Any object to check.

        Returns:
            Becomes the menu item enabled value.

        """
        return True

    def reload_items(self) -> None:
        """Empty all items in the menu and re-add them

        Only works if initialize_items is used

        :return: None
        """
        self._needs_refresh = True
        items = self.initialize_items()

        if items:
            self.menu_items.empty()

            for item in items:
                self.add(item)
                if item.enabled:
                    item.enabled = self.is_valid_entry(item.game_object)

            self.menu_items.arrange_menu_items()
            for index, item in enumerate(self.menu_items):
                # TODO: avoid introspection of the items to implement
                # different behavior
                if item.game_object.__class__.__name__ != "Monster":
                    break
                self.selected_index = index
                if item.enabled:
                    break

    def build_item(
        self: Menu[Callable[[], object]],
        label: str,
        callback: Callable[[], object],
        icon: Optional[pygame.surface.Surface] = None,
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

    def add(self, item: MenuItem[T]) -> None:
        """
        Add a menu item.

        Parameters:
            item: Menu item to add.

        """
        self.menu_items.add(item)
        self._needs_refresh = True

    def clear(self) -> None:
        """
        Clears all menu items
        """
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
        self.menu_select_sound = audio.load_sound(
            self.menu_select_sound_filename,
        )

    def shadow_text(
        self,
        text: str,
        bg: ColorLike = (192, 192, 192),
        fg: Optional[ColorLike] = None,
    ) -> pygame.surface.Surface:
        """
        Draw shadowed text.

        Parameters:
            text: Text to draw.
            bg: Background color.
            fg: Foreground color.

        Returns:
            Surface with the drawn text.

        """
        color = fg
        if not color:
            color = self.font_color

        top = self.font.render(text, True, color)
        shadow = self.font.render(text, True, bg)

        offset = layout((0.5, 0.5))
        size = [int(math.ceil(a + b)) for a, b in zip(offset, top.get_size())]
        image = pygame.Surface(size, pygame.SRCALPHA)

        image.blit(shadow, offset)
        image.blit(top, (0, 0))
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

    def draw(
        self,
        surface: pygame.surface.Surface,
    ) -> None:
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
        color: ColorLike = (10, 10, 10),
        line_spacing: int = 10,
    ) -> None:
        """
        Set the font properties that the menu uses.

        The size and line_spacing parameters will be adjusted the
        the screen scale.  You should pass the original, unscaled values.

        Parameters:
            size: The font size in pixels.
            font: Path to the typeface file (.ttf).
            color: Font color.
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

        self.font_color = color
        self.font = pygame.font.Font(font, self.font_size)

    def calc_internal_rect(self) -> pygame.rect.Rect:
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
            event.pressed and self.state == "normal"
            and not disabled and self.menu_items
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
                        a - b for a, b in zip(
                            mouse_pos,
                            self.menu_items.rect.topleft,
                        )
                    ]

                for index, item in enumerate([
                    i for i in self.menu_items if i.enabled
                ]):
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
            previous.in_focus = False  # clear the focus flag of old item, if any
        self.selected_index = index  # update the selection index
        self.menu_select_sound.play()  # play a sound
        self.trigger_cursor_update(animate)  # move cursor and [maybe] animate it
        selected = self.get_selected_item()
        assert selected
        selected.in_focus = True  # set focus flag of new item
        self.on_menu_selection_change()  # let subclass know menu has changed

    def search_items(self, game_object: Any) -> Optional[MenuItem[T]]:
        """
        Non-optimised search through menu_items for a particular thing.

        TODO: address the confusing name "game object".

        Parameters:
            game_object: Object to search in the menu.

        Returns:
            Menu item containing the object, if any.

        """
        for menu_item in self.menu_items:
            if game_object == menu_item.game_object:
                return menu_item
        return None

    def trigger_cursor_update(
        self,
        animate: bool = True,
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
            return self.animate(self.arrow.rect, right=x, centery=y, duration=self.cursor_move_duration)
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
        if self.state == "closed":

            def show_items() -> None:
                self.state = "normal"
                self._show_contents = True
                self.on_menu_selection_change()
                self.on_open()

            self.state = "opening"
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
                self.state = "normal"
                show_items()

    def close(self) -> None:
        if self.state in ["normal", "opening"]:
            self.state = "closing"
            ani = self.animate_close()
            if ani:
                ani.callback = self.client.pop_state
            else:
                self.client.pop_state()

    def anchor(self, attribute: str, value: Tuple[int, int]) -> None:
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

    def calc_menu_items_rect(self) -> pygame.rect.Rect:
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

    def calc_final_rect(self) -> pygame.rect.Rect:
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

    def on_menu_selection(self, item: MenuItem[T]) -> None:
        """
        Hook for things to happen when player selects a menu option.

        Override in subclass, if you want to.

        """
        if item.enabled:
            assert item.game_object is not None
            assert callable(item.game_object)
            item.game_object()

    def on_menu_selection_change(self) -> None:
        """
        Hook for things to happen after menu selection changes.

        Override in subclass.

        """

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

    def animate_open(self) -> Animation:

        # anchor the center of the popup
        rect = self.client.screen.get_rect()
        self.anchor("center", rect.center)

        rect = self.calc_final_rect()

        # set rect to a small size for the initial values of the animation
        self.rect = self.rect.copy()  # required.  do not remove.
        self.rect.height = int(rect.height * 0.1)
        self.rect.width = int(rect.width * 0.1)
        self.rect.center = rect.center

        # if this statement were removed, then the menu would
        # refresh and the size animation would be lost
        self._needs_refresh = False

        # create animation to open window with
        ani = self.animate(
            self.rect,
            height=rect.height,
            width=rect.width,
            duration=0.20,
        )
        ani.update_callback = lambda: setattr(self.rect, "center", rect.center)
        return ani
