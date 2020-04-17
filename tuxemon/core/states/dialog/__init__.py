from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from tuxemon.core.menu.menu import PopUpMenu
from tuxemon.core.platform.const import buttons
from tuxemon.core.ui.text import TextArea


class DialogState(PopUpMenu):
    """ Game state with a graphic box and some text in it

    Pressing the action button:
    * if text is being displayed, will cause text speed to go max
    * when text is displayed completely, then will show the next message
    * if there are no more messages, then the dialog will close
    """
    default_character_delay = .05

    def startup(self, **kwargs):
        super(DialogState, self).startup(**kwargs)
        self.text_queue = kwargs.get("text", list())
        self.avatar = kwargs.get("avatar", None)
        self.menu = kwargs.get("menu", None)
        self.text_area = TextArea(self.font, self.font_color)
        self.text_area.rect = self.calc_internal_rect()
        self.sprites.add(self.text_area)

        if self.avatar:
            avatar_rect = self.calc_final_rect()
            self.avatar.rect.bottomleft = avatar_rect.left, avatar_rect.top
            self.sprites.add(self.avatar)

    def on_open(self):
        self.next_text()

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
        if event.pressed and event.button == buttons.A:
            if self.text_area.drawing_text:
                self.character_delay = .001

            elif self.next_text() is None:
                if self.menu:
                    self.client.push_state("ChoiceState", menu=self.menu, rect=self.text_area.rect)
                else:
                    self.client.pop_state(self)

    def next_text(self):
        try:
            text = self.text_queue.pop(0)
            self.alert(text)
            return text
        except IndexError:
            return None
