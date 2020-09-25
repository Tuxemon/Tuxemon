from functools import partial

from tuxemon.compat import Rect
from tuxemon.core import tools
from tuxemon.core.menu.interface import MenuItem
from tuxemon.core.menu.menu import Menu
from tuxemon.core.platform.const import events
from tuxemon.core.ui.text import TextArea


class InputMenu(Menu):
    background = None
    draw_borders = False

    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890.-!"
    alphabet_length = 26

    def startup(self, *items, **kwargs):
        """

        Accepted Keyword Arguments:
            prompt:   String used to let user know what value is being inputted (ie "Name?", "IP Address?")
            callback: Function to be called when dialog is confirmed.  The value will be sent as only argument
            initial:  Optional string to pre-fill the input box with.

        :param items:
        :param kwargs:
        :return:
        """
        super().startup(*items, **kwargs)
        self.input_string = kwargs.get("initial", "")

        # area where the input will be shown
        self.text_area = TextArea(self.font, self.font_color, (96, 96, 96))
        self.text_area.animated = False
        self.text_area.rect = Rect(tools.scale_sequence([90, 30, 80, 100]))
        self.text_area.text = self.input_string
        self.sprites.add(self.text_area)

        # prompt
        self.prompt = TextArea(self.font, self.font_color, (96, 96, 96))
        self.prompt.animated = False
        self.prompt.rect = Rect(tools.scale_sequence([50, 20, 80, 100]))
        self.sprites.add(self.prompt)

        self.prompt.text = kwargs.get("prompt", "")
        self.callback = kwargs.get("callback")
        assert self.callback

    def calc_internal_rect(self):
        w = self.rect.width - self.rect.width * .8
        h = self.rect.height - self.rect.height * .5
        rect = self.rect.inflate(-w, -h)
        rect.top = self.rect.centery * .7
        return rect

    def initialize_items(self):
        self.menu_items.columns = self.alphabet_length // 2

        # add the keys
        for char in self.chars:
            yield MenuItem(self.shadow_text(char), None, None, partial(self.add_input_char, char))

        # backspace key
        yield MenuItem(self.shadow_text("←"), None, None, self.backspace)

        # button to confirm the input and close the dialog
        yield MenuItem(self.shadow_text("END"), None, None, self.confirm)

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
        event = super().process_event(event)

        if event and event.pressed:
            if event.button == events.BACKSPACE:
                self.backspace()
                return

            if event.button == events.UNICODE:
                char = event.value
                if char == " " or char in self.chars:
                    self.add_input_char(char)
                return

        return event

    def backspace(self):
        self.input_string = self.input_string[:-1]
        self.update_text_area()

    def add_input_char(self, char):
        self.input_string += char
        self.update_text_area()

    def update_text_area(self):
        self.text_area.text = self.input_string

    def confirm(self):
        """ Confirm the input

        This is called when user selects "End".  Override, maybe?

        :return:
        """
        self.callback(self.input_string)
        self.client.pop_state(self)
