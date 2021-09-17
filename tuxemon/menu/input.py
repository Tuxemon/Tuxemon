from __future__ import annotations
from functools import partial

from pygame.rect import Rect
from tuxemon import tools
from tuxemon.locale import T
from tuxemon.menu.interface import MenuItem
from tuxemon.menu.menu import Menu
from tuxemon.platform.const import events
from tuxemon.ui.text import TextArea
from typing import Any, Generator, Optional, Callable
from tuxemon.platform.events import PlayerInput


class InputMenu(Menu):
    background = None
    draw_borders = False

    def startup(
        self,
        *items: Any,
        prompt: str = "",
        callback: Optional[Callable[[str], None]] = None,
        initial: str = "",
        **kwargs: Any,
    ) -> None:
        """
        Initialize the input menu.

        Parameters:
            prompt:   String used to let user know what value is being
                inputted (ie "Name?", "IP Address?").
            callback: Function to be called when dialog is confirmed. The
                value will be sent as only argument.
            initial:  Optional string to pre-fill the input box with.

        """
        super().startup(*items, **kwargs)
        self.input_string = initial
        self.chars = T.translate("menu_alphabet").replace(r"\0", "\0")
        self.n_columns = int(T.translate("menu_alphabet_n_columns"))

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

        self.prompt.text = prompt
        self.callback = callback
        assert self.callback

    def calc_internal_rect(self) -> Rect:
        w = self.rect.width - self.rect.width * 0.8
        h = self.rect.height - self.rect.height * 0.5
        rect = self.rect.inflate(-w, -h)
        rect.top = int(self.rect.centery * 0.7)
        return rect

    def initialize_items(self) -> Generator[MenuItem, None, None]:
        self.menu_items.columns = self.n_columns

        # add the keys
        for char in self.chars:
            if char == "\0":
                empty = MenuItem(self.shadow_text(" "), None, None, None)
                empty.enabled = False
                yield empty
            else:
                yield MenuItem(
                    self.shadow_text(char),
                    None,
                    None,
                    partial(self.add_input_char, char),
                )

        # backspace key
        yield MenuItem(self.shadow_text("←"), None, None, self.backspace)

        # button to confirm the input and close the dialog
        yield MenuItem(self.shadow_text("END"), None, None, self.confirm)

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:

        maybe_event = super().process_event(event)

        if maybe_event and maybe_event.pressed:
            if maybe_event.button == events.BACKSPACE:
                self.backspace()
                return None

            if maybe_event.button == events.UNICODE:
                char = maybe_event.value
                if char == " " or char in self.chars:
                    self.add_input_char(char)
                return None

        return maybe_event

    def backspace(self) -> None:
        self.input_string = self.input_string[:-1]
        self.update_text_area()

    def add_input_char(self, char: str) -> None:
        self.input_string += char
        self.update_text_area()

    def update_text_area(self) -> None:
        self.text_area.text = self.input_string

    def confirm(self) -> None:
        """
        Confirm the input.

        This is called when user selects "End".  Override, maybe?

        """
        assert self.callback
        self.callback(self.input_string)
        self.client.pop_state(self)
