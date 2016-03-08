from __future__ import division

import pygame

from core.components.menu.menu import PopUpMenu
from core.components.ui.text import TextArea


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
        self.text_area = TextArea(self.font, self.font_color)
        self.text_area.rect = self.calc_internal_rect()
        self.sprites.add(self.text_area)

    def on_open(self):
        self.next_text()

    def process_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            if self.text_area.drawing_text:
                self.character_delay = .001

            elif self.next_text() is None:
                self.game.pop_state(self)

    def next_text(self):
        try:
            text = self.text_queue.pop(0)
            self.alert(text)
            return text
        except IndexError:
            return None
