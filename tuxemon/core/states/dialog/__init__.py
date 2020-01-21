from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from tuxemon.core import tools
from tuxemon.core.menu.menu import PopUpMenu
from tuxemon.core.ui.text import TextArea
from tuxemon.core.platform.const import buttons


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

    def on_open(self):
        self.next_text()
        self.draw_avatar()

    def process_event(self, event):
        """ Handles player input events. This function is only called when the
        player provides input such as pressing a key or clicking the mouse.

        Since this is part of a chain of event handlers, the return value
        from this method becomes input for the next one.  Returning None
        signifies that this method has dealt with an event and wants it
        exclusively.  Return the event and others can use it as well.

        You should return None if you have handled input here.

        :type event: core.input.PlayerInput
        :rtype: Optional[core.input.PlayerInput]
        """
        if event.pressed and event.button == buttons.A:
            if self.text_area.drawing_text:
                self.character_delay = .001

            elif self.next_text() is None:
                if self.menu:
                    self.game.push_state("ChoiceState", menu=self.menu, rect=self.text_area.rect)
                else:
                    self.game.pop_state(self)

    def next_text(self):
        try:
            text = self.text_queue.pop(0)
            self.alert(text)
            return text
        except IndexError:
            return None

    def draw_avatar(self):
        if not self.avatar:
            return

        # If the prefix is "monster" the second parameter refers to a monster
        # If this parameter is a number, we're referring to a monster slot in the party
        # If this parameter is a string, we're referring to a monster name
        # If there's no prefix, the parameter represents the path to a sprite file
        params = self.avatar.split(" ")
        if params[0] == "monster":
            if params[1].isdigit():
                player = self.game.player1
                slot = int(params[1])
                avatar_sprite = player.monsters[slot].menu_sprite
            else:
                avatar_sprite = "gfx/sprites/battle/{}-menu01.png".format(params[1])
        else:
            avatar_sprite = self.avatar

        avatar_rect = self.calc_final_rect()
        avatar_sprite = tools.load_sprite(avatar_sprite)
        avatar_sprite.rect.bottomleft = avatar_rect.left, avatar_rect.top
        self.sprites.add(avatar_sprite)
