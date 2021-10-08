from __future__ import annotations
from tuxemon.menu.interface import MenuItem
from tuxemon.menu.menu import PopUpMenu
from typing import Any, Generator, Callable, Tuple, Sequence


class ChoiceState(PopUpMenu):
    """
    Game state with a graphic box and some text in it.

    Pressing the action button:
    * if text is being displayed, will cause text speed to go max
    * when text is displayed completely, then will show the next message
    * if there are no more messages, then the dialog will close
    """

    shrink_to_items = True
    escape_key_exits = False

    def startup(
        self,
        *,
        menu: Sequence[Tuple[str, str, Callable[[], None]]] = (),
        escape_key_exits: bool = False,
        **kwargs: Any,
    ) -> None:
        super().startup(**kwargs)
        self.menu = menu
        self.escape_key_exits = escape_key_exits

    def initialize_items(self) -> None:
        for _key, label, callback in self.menu:
            image = self.shadow_text(label)
            item = MenuItem(image, label, None, callback)
            self.add(item)
