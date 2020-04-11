from __future__ import absolute_import
from __future__ import division, print_function
from __future__ import unicode_literals

import logging
import math
from functools import partial

import pygame

from tuxemon.core import audio, prepare, state, tools, graphics
from tuxemon.core.menu.interface import MenuCursor, MenuItem
from tuxemon.core.platform.const import buttons, intentions
from tuxemon.core.sprite import RelativeGroup, VisualSpriteList
from tuxemon.core.ui.draw import GraphicBox
from tuxemon.core.ui.text import TextArea

logger = logging.getLogger(__name__)


def layout(scale):
    def func(area):
        return [scale * i for i in area]

    return func


layout = layout(prepare.SCALE)


class Menu(state.State):
    """ A class to create menu objects.

    Menus are a type of game state.  Menus that are the top state
    will receive player input and respond to it.  They may be
    stacked, so that menus are nested.

    :background: String

    :ivar rect: The rect of the menu in pixels, defaults to 0, 0, 400, 200.
    :ivar state: An arbitrary state of the menu. E.g. "opening" or "closing".
    :ivar selected_index: The index position of the currently selected menu item.
    :ivar menu_items: A list of available menu items.
    """
    # defaults for the menu
    columns = 1
    min_font_size = 4
    draw_borders = True
    background = None                 # Image used to draw the background
    background_color = 248, 248, 248  # The window's background color
    unavailable_color = 220, 220, 220 # Font color when the action is unavailable
    background_filename = None        # File to load for image background
    menu_select_sound_filename = "sound_menu_select"
    font_filename = prepare.fetch("font", "PressStart2P.ttf")
    borders_filename = "gfx/dialog-borders01.png"
    cursor_filename = "gfx/arrow.png"
    cursor_move_duration = .20
    default_character_delay = 0.05
    shrink_to_items = False    # fit the border to contents
    escape_key_exits = True    # escape key closes menu
    animate_contents = False   # show contents while window opens
    touch_aware = True        # if true, then menu items can be selected with the mouse/touch

    def startup(self, *items, **kwargs):
        self.rect = self.rect.copy()  # do not remove!
        i = kwargs.get('selected_index', 0)
        self.selected_index = i       # track which menu item is selected
        self.state = "closed"         # closed, opening, normal, disabled, closing
        self.window = None            # draws borders, background
        self._show_contents = False   # draw menu items, or not
        self._needs_refresh = False   # refresh layout on next draw
        self._anchors = dict()        # used to position the menu/state
        self.__dict__.update(kwargs)  # may be removed in the future

        # holds sprites representing menu items
        self.create_new_menu_items_group()

        self.set_font()          # load default font
        self.load_graphics()     # load default graphics
        self.reload_sounds()     # load default sounds

    def create_new_menu_items_group(self):
        """ Create a new group for menu items to be contained in

        Override if you need special placement for the menu items.

        :return: None
        """
        # contains the selectable elements of the menu
        self.menu_items = VisualSpriteList(parent=self.calc_menu_items_rect)
        self.menu_items.columns = self.columns

        # generally just for the cursor arrow
        self.menu_sprites = RelativeGroup(parent=self.menu_items)

    def shutdown(self):
        """ Clear objects likely to cause cyclical references

        :returns: None
        """
        self.sprites.empty()
        self.menu_items.empty()
        self.menu_sprites.empty()
        self.animations.empty()

        self.client.release_controls()

        del self.arrow
        del self.menu_items
        del self.menu_sprites

    def start_text_animation(self, text_area, callback):
        """ Start an animation to show textarea, one character at a time

        :param text_area: TextArea to animate
        :type text_area: tuxemon.core.ui.text.TextArea
        :param callback: called when alert is complete
        :type callback: callable
        :rtype: None
        """

        def next_character():
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

    def animate_text(self, text_area, text, callback):
        """ Set and animate a text area

        :param text: Test to display
        :type text: basestring
        :param text_area: TextArea to animate
        :type text_area: tuxemon.core.ui.text.TextArea
        :param callback: called when alert is complete
        :type callback: callable
        :rtype: None
        """
        text_area.text = text
        self.start_text_animation(text_area, callback)

    def alert(self, message, callback=None):
        """ Write a message to the first available text area

        Generally, a state will have just one, if any, text area.
        The first one found will be use to display the message.
        If no text area is found, a RuntimeError will be raised

        :param message: Something interesting, I hope.
        :type message: basestring
        :param callback: called when alert is complete
        :type callback: callable

        :returns: None
        """

        def find_textarea():
            for sprite in self.sprites:
                if isinstance(sprite, TextArea):
                    return sprite
            logger.error("attempted to use 'alert' on state without a TextArea", message)
            raise RuntimeError

        self.animate_text(find_textarea(), message, callback)

    def initialize_items(self):
        """ Advanced way to fill in menu items

        For menus that change dynamically, use of this method will
        make changes to the menu easier.

        :return:
        """
        pass

    def is_valid_entry(self, game_object):
        """ Checked when items are loaded/reloaded.  The return value will enable/disable menu items

        WIP.  The value passed should be Item.game_object

        :param Any game_object: Any object to check
        :return boolean: Becomes the menu item enabled value
        """
        return True

    def reload_items(self):
        """ Empty all items in the menu and re-add them

        Only works if initialize_items is used

        :return: None
        """
        self._needs_refresh = True
        items = self.initialize_items()
        if items:
            self.menu_items.empty()

            for item in items:
                self.add(item)
                item.enabled = self.is_valid_entry(item.game_object)

            if hasattr(self.menu_items, "arrange_menu_items"):
                self.menu_items.arrange_menu_items()

            for index, item in enumerate(self.menu_items):
                self.selected_index = index
                if item.enabled:
                    break

    def build_item(self, label, callback, icon=None):
        """ Create a menu item and add it to the menu

        :param label: Some text
        :param icon: pygame surface (not used yet)
        :param callback: callback to use when selected
        :return: Menu Item
        """
        image = self.shadow_text(label)
        item = MenuItem(image, label, None, callback)
        self.add(item)

    def add(self, item):
        """ Add a menu item

        :type item: tuxemon.core.menu.MenuItem
        :return: None
        """
        self.menu_items.add(item)
        self._needs_refresh = True

    def fit_border(self):
        """ Resize the window border to fit the contents of the menu

        :return:
        """
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

    def reload_sounds(self):
        """ Reload sounds

        :returns: None
        """
        self.menu_select_sound = audio.load_sound(self.menu_select_sound_filename)

    def shadow_text(self, text, bg=(192, 192, 192), fg=None):
        """ Draw shadowed text

        :param text: Text to draw
        :param bg:
        :returns:
        """
        color = fg
        if not color:
            color = self.font_color

        top = self.font.render(text, 1, color)
        shadow = self.font.render(text, 1, bg)

        offset = layout((0.5, 0.5))
        size = [int(math.ceil(a + b)) for a, b in zip(offset, top.get_size())]
        image = pygame.Surface(size, pygame.SRCALPHA)

        image.blit(shadow, offset)
        image.blit(top, (0, 0))
        return image

    def load_graphics(self):
        """ Loads all the graphical elements of the menu
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

    def show_cursor(self):
        """ Show the cursor that indicates the selected object

        :returns: None
        """
        if self.arrow not in self.menu_sprites:
            self.menu_sprites.add(self.arrow)
        self.trigger_cursor_update(False)
        self.get_selected_item().in_focus = True

    def hide_cursor(self):
        """ Hide the cursor that indicates the selected object

        :returns: None
        """
        if self.arrow in self.menu_sprites:
            self.menu_sprites.remove(self.arrow)
            selected = self.get_selected_item()
            if selected is not None:
                selected.in_focus = False

    def refresh_layout(self):
        """ Fit border to contents and hide/show cursor

        :return:
        """
        self.menu_items.expand = not self.shrink_to_items

        # check if we have items, but they are all disabled
        disabled = all(not i.enabled for i in self.menu_items)

        if self.menu_items and not disabled:
            self.show_cursor()
        else:
            self.hide_cursor()

        if self.shrink_to_items:
            self.fit_border()

    def draw(self, surface):
        """ Draws the menu object to a pygame surface.

        :param surface: Surface to draw on
        :type surface: pygame.Surface

        :rtype: None
        :returns: None

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

        # debug = show the menu items area
        # surface.fill((255, 0, 0), self.calc_internal_rect(), 2)

    def set_font(self, size=5, font=None, color=(10, 10, 10), line_spacing=10):
        """Set the font properties that the menu uses including font _color, size, typeface,
        and line spacing.

        The size and line_spacing parameters will be adjusted the
        the screen scale.  You should pass the original, unscaled values.

        :param size: The font size in pixels.
        :param font: Path to the typeface file (.ttf)
        :param color: A tuple of the RGB _color values
        :param line_spacing: The spacing in pixels between lines of text

        :type size: Integer
        :type font: String
        :type color: Tuple
        :type line_spacing: Integer

        :rtype: None
        :returns: None

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

    def calc_internal_rect(self):
        """ Calculate the area inside the borders, if any.
        If no borders are present, a copy of the menu rect will be returned

        :returns: Rect representing space inside borders, if any
        :rtype: Rect
        """
        return self.window.calc_inner_rect(self.rect)

    def process_event(self, event):
        """ Handles player input events. This function is only called when the
        player provides input such as pressing a key or clicking the mouse.

        Since this is part of a chain of event handlers, the return value
        from this method becomes input for the next one.  Returning None
        signifies that this method has dealt with an event and wants it
        exclusively.  Return the event and others can use it as well.

        You should return None if you have handled input here.

        :type event: tuxemon.core.input.PlayerInput
        :rtype: Optional[core.input.PlayerInput]
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
        valid_change = event.pressed and self.state == "normal" and not disabled and self.menu_items

        # confirm selection
        if event.button in (buttons.A, intentions.SELECT):
            handled_event = True
            if valid_change:
                self.menu_select_sound.play()
                self.on_menu_selection(self.get_selected_item())

        # cursor movement
        if event.button in (buttons.UP, buttons.DOWN, buttons.LEFT, buttons.RIGHT):
            handled_event = True
            if valid_change:
                index = self.menu_items.determine_cursor_movement(self.selected_index, event)
                if not self.selected_index == index:
                    self.change_selection(index)

        # mouse/touch selection
        if event.button in (buttons.MOUSELEFT, ):
            handled_event = True
            # TODO: handling of click/drag, miss-click, etc
            # TODO: eventually, maybe move some handling into menuitems
            # TODO: handle screen scaling?
            # TODO: generalized widget system
            if self.touch_aware and valid_change:
                mouse_pos = event.value
                assert mouse_pos is not 0

                try:
                    self.menu_items.update_rect_from_parent()
                except AttributeError:
                    pass
                else:
                    mouse_pos = [a - b for a, b in zip(mouse_pos, self.menu_items.rect.topleft)]

                for index, item in enumerate([i for i in self.menu_items if i.enabled]):
                    if item.rect.collidepoint(mouse_pos):
                        self.change_selection(index)
                        self.on_menu_selection(self.get_selected_item())

        if not handled_event:
            return event

    def change_selection(self, index, animate=True):
        """ Force the menu to be evaluated and move cursor and trigger focus changes

        :return: None
        """
        previous = self.get_selected_item()
        if previous is not None:
            previous.in_focus = False              # clear the focus flag of old item, if any
        self.selected_index = index                # update the selection index
        self.menu_select_sound.play()              # play a sound
        self.trigger_cursor_update(animate)        # move cursor and [maybe] animate it
        self.get_selected_item().in_focus = True   # set focus flag of new item
        self.on_menu_selection_change()            # let subclass know menu has changed

    def search_items(self, game_object):
        """ Non-optimised search through menu_items for a particular thing

        TODO: address the confusing name "game object"

        :param game_object:
        :return:
        """
        for menu_item in self.menu_items:
            if game_object == menu_item.game_object:
                return menu_item
        return None

    def trigger_cursor_update(self, animate=True):
        """ Force the menu cursor to move into the correct position

        :param animate: If True, then arrow will move smoothly into position
        :returns: None or Animation
        """
        selected = self.get_selected_item()
        if not selected:
            return

        x, y = selected.rect.midleft
        x -= tools.scale(2)

        if animate:
            self.remove_animations_of(self.arrow.rect)
            return self.animate(self.arrow.rect, right=x, centery=y, duration=self.cursor_move_duration)
        else:
            self.arrow.rect.midright = x, y
            return None

    def get_selected_item(self):
        """ Get the Menu Item that is currently selected

        :rtype: MenuItem
        :rtype: tuxemon.core.menu.interface.MenuItem
        """
        try:
            return self.menu_items[self.selected_index]
        except IndexError:
            return None

    def resume(self):
        if self.state == "closed":
            def show_items():
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
                    ani.update_callback = partial(setattr, self.menu_items, "_needs_arrange", True)
                ani.callback = show_items
            else:
                self.state = "normal"
                show_items()

    def close(self):
        if self.state in ["normal", "opening"]:
            self.state = "closing"
            ani = self.animate_close()
            if ani:
                ani.callback = self.client.pop_state
            else:
                self.client.pop_state()

    def anchor(self, attribute, value):
        """ Set an anchor for the menu window

        You can pass any string value that is used in a pygame rect,
        for example: "center", "topleft", and "right".

        When changes are made to the window or it is being opened
        or sized, then these values passed as anchors will override
        others.  The order of which each anchor is applied is not
        necessarily going to match the order they were set, as the
        implementation relies on a dictionary.

        Take care to make sure values do not overlap.

        :param attribute:
        :param value:
        :return:
        """
        if value is None:
            del self._anchors[attribute]
        else:
            self._anchors[attribute] = value

    def position_rect(self):
        """ Reposition rect taking in account the anchors
        """
        for attribute, value in self._anchors.items():
            setattr(self.rect, attribute, value)

    # ============================================================================
    #   The following methods are designed to be monkey patched or overloaded
    # ============================================================================

    def calc_menu_items_rect(self):
        """ Calculate the area inside the internal rect where items are listed

        :rtype: Rect
        """
        # WARNING: hardcoded values related to menu arrow size
        #          if menu arrow image changes, this should be adjusted
        cursor_margin = -tools.scale(11), -tools.scale(5)
        inner = self.calc_internal_rect()
        menu_rect = inner.inflate(*cursor_margin)
        menu_rect.bottomright = inner.bottomright
        return menu_rect

    def calc_final_rect(self):
        """ Calculate the area in the game window where menu is shown

        This value is the __desired__ location and size, and should not change
        over the lifetime of the menu.  It is used to generate animations
        to open the menu.

        The rect represents the size of the menu after all items are added.

        :rtype: Rect
        """
        original = self.rect.copy()    # store the original rect
        self.refresh_layout()          # arrange the menu
        rect = self.rect.copy()        # store the final rect
        self.rect = original           # set the original back
        return rect

    def on_open(self):
        """ Hook is called after opening animation has finished

        :return:
        """
        pass

    def on_menu_selection(self, item):
        """ Hook for things to happen when player selects a menu option

        Override in subclass, if you want to

        :return:
        """
        if item.enabled:
            item.game_object()

    def on_menu_selection_change(self):
        """ Hook for things to happen after menu selection changes

        Override in subclass

        :returns: None
        """
        pass

    def animate_open(self):
        """ Called when menu is going to open

        Menu will not receive input during the animation
        Menu will only play this animation once

        Must return either an Animation or Task to attach callback
        Only modify state of the menu Rect
        Do not change important state attributes

        :returns: Animation or Task
        :rtype: tuxemon.core.animation.Animation
        """
        return None

    def animate_close(self):
        """ Called when menu is going to open

        Menu will not receive input during the animation
        Menu will play animation only once
        Menu will be popped after animation finished

        Must return either an Animation or Task to attach callback
        Only modify state of the menu Rect
        Do not change important state attributes

        :returns: Animation or Task
        :rtype: tuxemon.core.animation.Animation
        """
        return None


class PopUpMenu(Menu):
    """ Menu with "pop up" style animation

    """

    def animate_open(self):
        """ Called when menu is going to open

        Menu will not receive input during the animation
        Menu will only play this animation once

        Must return either an Animation or Task to attach callback
        Only modify state of the menu Rect
        Do not change important state attributes

        :returns: Animation or Task
        :rtype: tuxemon.core.animation.Animation
        """
        # anchor the center of the popup
        rect = self.client.screen.get_rect()
        self.anchor("center", rect.center)

        rect = self.calc_final_rect()

        # set rect to a small size for the initial values of the animation
        self.rect = self.rect.copy()           # required.  do not remove.
        self.rect.height = int(rect.height * .1)
        self.rect.width = int(rect.width * .1)
        self.rect.center = rect.center

        # if this statement were removed, then the menu would
        # refresh and the size animation would be lost
        self._needs_refresh = False

        # create animation to open window with
        ani = self.animate(self.rect, height=rect.height, width=rect.width, duration=.20)
        ani.update_callback = lambda: setattr(self.rect, "center", rect.center)
        return ani
