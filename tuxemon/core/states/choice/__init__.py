from tuxemon.core.menu.interface import MenuItem
from tuxemon.core.menu.menu import PopUpMenu


class ChoiceState(PopUpMenu):
    """ Game state with a graphic box and some text in it

    Pressing the action button:
    * if text is being displayed, will cause text speed to go max
    * when text is displayed completely, then will show the next message
    * if there are no more messages, then the dialog will close
    """
    shrink_to_items = True
    escape_key_exits = None

    def startup(self, **kwargs):
        super().startup(**kwargs)
        self.menu = kwargs.get("menu", list())
        self.escape_key_exits = kwargs.get("escape_key_exits", False)

    def initialize_items(self):
        for key, label, callback in self.menu:
            image = self.shadow_text(label)
            item = MenuItem(image, label, None, callback)
            self.add(item)
