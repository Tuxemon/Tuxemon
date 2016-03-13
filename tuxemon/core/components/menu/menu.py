from __future__ import division
from __future__ import print_function

import math

import pygame

from core import state, prepare, tools
from core.components.menu.interface import MenuCursor
from core.components.sprite import VisualSpriteList, RelativeGroup
from core.components.ui.draw import GraphicBox
from core.components.ui.text import TextArea


def layout(scale):
    def func(area):
        return [scale * i for i in area]

    return func


layout = layout(prepare.SCALE)


class Menu(state.State):
    """A class to create menu objects.

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
    background = None
    background_color = 248, 248, 248  # The window's background 	olor
    background_filename = None
    menu_select_sound_filename = "sounds/interface/menu-select.ogg"
    font_filename = "resources/font/PressStart2P.ttf"
    borders_filename = "gfx/dialog-borders01.png"
    cursor_filename = "gfx/arrow.png"
    cursor_move_duration = .20
    default_character_delay = 0.05
    shrink_to_items = False
    escape_key_exits = True

    def startup(self, *items, **kwargs):
        self.rect = self.rect.copy()  # do not remove!

        self.__dict__.update(kwargs)

        # used to position the menu/state
        self._anchors = dict()

        # holds sprites representing menu items
        self.menu_items = VisualSpriteList(parent=self.calc_menu_items_rect)
        self.menu_items.columns = self.columns
        if self.shrink_to_items:
            self.menu_items.expand = False

        # generally just for the cursor arrow
        self.menu_sprites = RelativeGroup(parent=self.menu_items)

        self.selected_index = 0  # Used to track which menu item is selected
        self.state = "closed"    # closed, opening, normal, closing

        self.set_font()       # load default font
        self.load_graphics()  # load default graphics
        self.reload_sounds()  # load default sounds

    def shutdown(self):
        """ Clear objects likely to cause cyclical references

        :returns: None
        """
        self.sprites.empty()
        self.menu_items.empty()
        self.menu_sprites.empty()
        self.animations.empty()

        del self.arrow
        del self.menu_items
        del self.menu_sprites

    def start_text_animation(self, text_area):
        """ Start an animation to show textarea, one character at a time

        :param text_area: TextArea to animate
        :type text_area: core.components.ui.text.TextArea
        :rtype: None
        """
        def next_character():
            try:
                next(text_area)
            except StopIteration:
                pass
            else:
                self.task(next_character, self.character_delay)

        self.character_delay = self.default_character_delay
        self.remove_animations_of(next_character)
        next_character()

    def animate_text(self, text_area, text):
        """ Set and animate a text area

        :param text: Test to display
        :type text: basestring
        :param text_area: TextArea to animate
        :type text_area: core.components.ui.text.TextArea
        :rtype: None
        """
        text_area.text = text
        self.start_text_animation(text_area)

    def alert(self, message):
        """ Write a message to the first available text area

        Generally, a state will have just one, if any, text area.
        The first one found will be use to display the message.
        If no text area is found, a RuntimeError will be raised

        :param message: Something interesting, I hope.
        :type message: basestring

        :returns: None
        """
        def find_textarea():
            for sprite in self.sprites:
                if isinstance(sprite, TextArea):
                    return sprite
            print("attempted to use 'alert' on state without a TextArea", message)
            raise RuntimeError

        self.animate_text(find_textarea(), message)

    def _initialize_items(self):
        """ Internal use only.  Will reset the items in the menu

        Reset the menu items and get new updated ones.

        :rtype: collections.Iterable[MenuItem]
        """
        self.selected_index = 0
        self.menu_items.empty()
        for item in self.initialize_items():
            self.menu_items.add(item)
        if self.menu_items:
            self.show_cursor()

        # call item selection change to trigger callback for first time
        self.on_menu_selection_change()

        if self.shrink_to_items:
            center = self.rect.center
            rect1 = self.menu_items.calc_bounding_rect()
            rect2 = self.menu_sprites.calc_bounding_rect()
            rect1 = rect1.union(rect2)

            # TODO: do not hardcode these values
            # border is 12, padding is the rest
            rect1.width += tools.scale(18)
            rect1.height += tools.scale(19)
            rect1.topleft = 0, 0

            # self.rect = rect1.union(rect2)
            # self.rect.width += tools.scale(20)
            # self.rect.topleft = 0, 0
            self.rect = rect1
            self.rect.center = center
            self.position_rect()

    def reload_sounds(self):
        """ Reload sounds

        :returns: None
        """
        self.menu_select_sound = tools.load_sound(self.menu_select_sound_filename)

    def shadow_text(self, text, bg=(192, 192, 192)):
        """ Draw shadowed text

        :param text: Text to draw
        :param bg:
        :returns:
        """
        top = self.font.render(text, 1, self.font_color)
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
        # load and scale the _background
        background = None
        if self.background_filename:
            background = tools.load_image(self.background_filename)

        # load and scale the menu borders
        border = None
        if self.draw_borders:
            border = tools.load_and_scale(self.borders_filename)

        # set the helper to draw the _background
        self.window = GraphicBox(border, background, self.background_color)

        # handle the arrow cursor
        image = tools.load_and_scale(self.cursor_filename)
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
        self.menu_sprites.remove(self.arrow)
        self.get_selected_item().in_focus = False

    def draw(self, surface):
        """ Draws the menu object to a pygame surface.

        :param surface: Surface to draw on
        :type surface: pygame.Surface

        :rtype: None
        :returns: None

        """
        self.window.draw(surface, self.rect)

        if self.state == "normal" and self.menu_items:
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
            font = prepare.BASEDIR + self.font_filename

        if size < self.min_font_size:
            size = self.min_font_size

        self.line_spacing = tools.scale(line_spacing)
        self.font_size = tools.scale(size)
        self.font_color = color
        self.font = pygame.font.Font(font, self.font_size)

    def calc_internal_rect(self):
        """ Calculate the area inside the borders, if any.
        If no borders are present, a copy of the menu rect will be returned

        :returns: Rect representing space inside borders, if any
        :rtype: pygame.Rect
        """
        return self.window.calc_inner_rect(self.rect)

    def process_event(self, event):
        """ Process pygame input events

        The menu cursor is handled here, as well as the ESC and ENTER keys.

        This will also toggle the 'in_focus' of the menu item

        :param event: pygame.Event
        :returns: None
        """
        if event.type == pygame.KEYDOWN:
            if self.escape_key_exits and event.key == pygame.K_ESCAPE:
                self.close()
                return

            elif self.state == "normal" and self.menu_items and event.key == pygame.K_RETURN:
                self.menu_select_sound.play()
                self.on_menu_selection(self.get_selected_item())
                return

        # check if cursor has changed
        index = self.menu_items.determine_cursor_movement(self.selected_index, event)
        if not self.selected_index == index:
            self.get_selected_item().in_focus = False  # clear the focus flag of old item
            self.selected_index = index                # update the selection index
            self.menu_select_sound.play()
            self.trigger_cursor_update()               # move cursor and animate it
            self.get_selected_item().in_focus = True   # set focus flag of new item
            self.on_menu_selection_change()            # let subclass know menu has changed

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
        :rtype: core.components.menu.interface.MenuItem
        """
        try:
            return self.menu_items[self.selected_index]
        except IndexError:
            return None

    def resume(self):
        if self.state == "closed":
            def show_items():
                self.state = "normal"
                self.on_open()

            self._initialize_items()
            self.state = "opening"
            self.position_rect()
            ani = self.animate_open()
            if ani:
                ani.callback = show_items
            else:
                show_items()

    def close(self):
        if self.state in ["normal", "opening"]:
            self.state = "closing"
            ani = self.animate_close()
            if ani:
                ani.callback = self.game.pop_state
            else:
                self.game.pop_state()

    def anchor(self, attribute, value):
        """ Set an anchor for the menu window

        You can pass any string value that is used in a pygame rect,
        for example: "center", "topleft", and "right.

        When changes are made to the window, when it is being opened
        or sized, then these values passed as anchors will override
        others.  The order of which each anchor is applied is not
        necessarily going to match the order they were set, as the
        implementation relies on a dictionary.

        Take care to make sure values do not overlap,

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

    def update(self, time_delta):
        self.animations.update(time_delta)

    # ============================================================================
    #   The following methods are designed to be monkey patched or overloaded
    # ============================================================================

    def calc_menu_items_rect(self):
        """ Calculate the area inside the internal rect where items are listed

        :rtype: pygame.Rect
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

        This value is the __desired__ location, and should not change
        over the lifetime of the menu.  It is used to generate animations
        to open the menu.

        By default, this will be the entire screen

        :rtype: pygame.Rect
        """
        return self.rect

    def on_open(self):
        """ Hook is called after opening animation has finished

        :return:
        """
        pass

    def on_menu_selection(self, item):
        """ Hook for things to happen when player selects a menu option

        Override in subclass

        :return:
        """
        pass

    def on_menu_selection_change(self):
        """ Hook for things to happen after menu selection changes

        Override in subclass

        :returns: None
        """
        pass

    def initialize_items(self):
        """ Hook for adding items to menu when menu is created

        Override with a generator

        :returns: Generator of MenuItems
        :rtype: collections.Iterable[MenuItem]
        """
        return iter(())

    def animate_open(self):
        """ Called when menu is going to open

        Menu will not receive input during the animation
        Menu will only play this animation once

        Must return either an Animation or Task to attach callback
        Only modify state of the menu Rect
        Do not change important state attributes

        :returns: Animation or Task
        :rtype: core.components.animation.Animation
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
        :rtype: core.components.animation.Animation
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
        :rtype: core.components.animation.Animation
        """
        # anchor the center of the popup
        rect = self.game.screen.get_rect()
        self.anchor("center", rect.center)

        rect = self.calc_final_rect()

        # set rect to a small size for the initial values of the animation
        self.rect = self.rect.copy()           # required.  do not remove.
        self.rect.height = rect.height / 2
        self.rect.width = rect.width / 2
        self.rect.center = rect.center

        # create animation to open window with
        ani = self.animate(self.rect, height=rect.height, width=rect.width, duration=.15)
        ani.update_callback = lambda: setattr(self.rect, "center", rect.center)
        return ani

    def animate_close(self):
        """ Called when menu is going to close

        Menu will not receive input during the animation
        Menu will play animation only once
        Menu will be popped after animation finished

        Must return either an Animation or Task to attach callback
        Only modify state of the menu Rect
        Do not change important state attributes

        :returns: Animation or Task
        :rtype: core.components.animation.Animation
        """
        # TODO: find a nice animation.  this one looks funny
        # self.menu_items.empty()
        # self.menu_sprites.empty()
        # self.animations.empty()
        #
        #
        # # set rect to a small size for the initial values of the animation
        # rect = self.rect.copy()
        # rect.height *= .2
        # rect.width *= .2
        # rect.center = self.rect.center
        #
        # # create animation to open window with
        # ani = Animation(height=rect.height, width=rect.width, duration=.15)
        # ani.start(self.rect)
        # ani.update_callback = lambda: setattr(self.rect, "center", rect.center)
        #
        # return ani
