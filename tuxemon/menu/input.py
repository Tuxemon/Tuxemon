# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random as rd
from collections.abc import Callable, Generator
from functools import partial
from typing import Any, Optional

import yaml
from pygame.rect import Rect

from tuxemon import tools
from tuxemon.constants import paths
from tuxemon.locale import T
from tuxemon.menu.interface import MenuItem
from tuxemon.menu.menu import Menu
from tuxemon.platform.const import buttons, events, intentions
from tuxemon.platform.events import PlayerInput
from tuxemon.session import local_session
from tuxemon.ui.text import TextArea


def load_names(file_path: str) -> Any:
    yaml_path = paths.mods_folder / file_path
    with yaml_path.open() as file:
        return yaml.safe_load(file)


class InputMenuObj:
    def __init__(
        self,
        action: Callable[[], None],
        char: Optional[str] = None,
    ):
        self.action = action
        self.char = char

    def __call__(self) -> None:
        return self.action()


class InputMenu(Menu[InputMenuObj]):
    """Menu used to input text."""

    background = None
    draw_borders = False

    def __init__(
        self,
        prompt: str = "",
        callback: Optional[Callable[[str], None]] = None,
        initial: str = "",
        char_limit: int = 99,
        random: bool = False,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the input menu.

        Parameters:
            prompt: String used to let user know what value is being
                inputted (ie "Name?", "IP Address?").
            callback: Function to be called when dialog is confirmed. The
                value will be sent as only argument.
            initial: Optional string to pre-fill the input box with.

        """
        self.name_data = load_names("npc_names.yaml")
        super().__init__(**kwargs)
        self.is_first_input = True
        self.input_string = initial
        self.chars = T.translate("menu_alphabet").replace(r"\0", "\0")
        self.char_variants = {
            s[0]: s[1:] for s in T.translate("menu_char_variants").split("\n")
        }
        self.all_chars = self.chars + "".join(
            v for v in self.char_variants.values()
        )
        # The following is necessary to prevent writing a char immediately
        # after leaving the char variant dialog.
        self.leaving_char_variant_dialog = False

        # area where the input will be shown
        self.text_area = TextArea(self.font, self.font_color, (96, 96, 96))
        self.text_area.animated = False
        self.text_area.rect = Rect(tools.scale_sequence((90, 30, 80, 100)))
        self.text_area.text = self.input_string
        self.sprites.add(self.text_area)

        # prompt
        self.prompt = TextArea(self.font, self.font_color, (96, 96, 96))
        self.prompt.animated = False
        self.prompt.rect = Rect(tools.scale_sequence((50, 20, 80, 100)))
        self.sprites.add(self.prompt)

        self.prompt.text = prompt
        self.callback = callback
        self.char_limit = char_limit
        self.random = random
        assert self.callback

        # Character counter
        self.char_counter = TextArea(self.font, self.font_color, (96, 96, 96))
        self.char_counter.animated = False
        self.update_char_counter()

        self.char_counter.rect.topleft = (
            int(self.text_area.rect.right + (self.rect.width * 0.25)),
            self.text_area.rect.top,
        )
        self.sprites.add(self.char_counter)

    def calc_internal_rect(self) -> Rect:
        w = self.rect.width - self.rect.width * 0.95
        h = self.rect.height - self.rect.height * 0.5
        rect = self.rect.inflate(-w, -h)
        rect.top = int(self.rect.centery * 0.7)
        return rect

    def initialize_items(
        self,
    ) -> Generator[MenuItem[InputMenuObj], None, None]:
        self.menu_items.columns = max(
            1, self.rect.width // int(self.rect.width * 0.075)
        )

        # add the keys
        for char in self.chars:
            if char == "\0":
                yield self._create_empty_item()
            else:
                yield self._create_char_item(char)

        # backspace key
        yield MenuItem(
            self.shadow_text("←"),
            None,
            None,
            InputMenuObj(self.backspace),
        )

        # button to confirm the input and close the dialog
        yield MenuItem(
            self.shadow_text("END"),
            None,
            None,
            InputMenuObj(self.confirm),
        )

        # random names
        if self.random:
            yield MenuItem(
                self.shadow_text(T.translate("dont_care")),
                None,
                None,
                InputMenuObj(self.dont_care),
            )

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        if event.button in (buttons.A, intentions.SELECT):
            self._handle_select_event(event)
            return None
        if event.pressed and event.button == events.BACKSPACE:
            self._handle_backspace_event()
            return None
        if event.pressed and event.button == events.UNICODE:
            self._handle_unicode_event(event.value)
            return None
        return super().process_event(event)

    def empty(self) -> None:
        pass

    def backspace(self) -> None:
        self.input_string = self.input_string[:-1]
        self.update_text_area()
        self.update_char_counter()

    def add_input_char_and_pop(self, char: str) -> None:
        self.leaving_char_variant_dialog = True
        self.add_input_char(char)
        self.client.pop_state()

    def add_input_char(self, char: str) -> None:
        if self.char_limit is None or len(self.input_string) < self.char_limit:
            # removes A at the end of the name
            self.input_string += char if not self.is_first_input else ""
            self.is_first_input = False
            self.update_text_area()
            self.update_char_counter()
        else:
            self.text_area.text = T.translate("alert_text")
            self.update_char_counter()

    def update_text_area(self) -> None:
        self.text_area.text = self.input_string

    def update_char_counter(self) -> None:
        remaining = max(0, self.char_limit - len(self.input_string))
        self.char_counter.text = f"{remaining}"

    def confirm(self) -> None:
        """
        Confirm the input.

        This is called when user selects "End".  Override, maybe?

        """
        if not self.text_area.text:
            return
        if self.callback is None:
            raise ValueError("Callback function not provided!")
        self.callback(self.input_string)
        self.client.pop_state(self)

    def dont_care(self) -> None:
        """
        Assigns the user a random name.
        This is called when the user selects "Don't Care".
        """
        variables = local_session.player.game_variables
        gender = variables.get("gender_choice", "neutral")
        if gender not in ["male", "female"]:
            gender = "neutral"
        language = T.get_current_language().lower()
        self.input_string = self.get_random_name(gender, language)
        self.update_text_area()

    def get_random_name(self, gender: str, language: str) -> str:
        try:
            name = rd.choice(self.name_data["random_names"][language][gender])
        except KeyError:
            default = self.client.config.locale.slug.lower()
            try:
                name = rd.choice(
                    self.name_data["random_names"][default][gender]
                )
            except KeyError:
                raise ValueError(
                    f"Names not found for language '{language}' "
                    f"or fallback language '{default}' and gender '{gender}'."
                )
        return str(name)

    def _create_empty_item(self) -> MenuItem[InputMenuObj]:
        empty = MenuItem(
            self.shadow_text(" "),
            None,
            None,
            InputMenuObj(self.empty),
        )
        empty.enabled = False
        return empty

    def _create_char_item(self, char: str) -> MenuItem[InputMenuObj]:
        return MenuItem(
            self.shadow_text(char),
            None,
            None,
            InputMenuObj(partial(self.add_input_char, char), char),
        )

    def _handle_select_event(self, event: PlayerInput) -> None:
        menu_item = self.get_selected_item()
        if menu_item is None:
            return
        if event.triggered:
            if self.leaving_char_variant_dialog:
                self.leaving_char_variant_dialog = False
            else:
                menu_item.game_object()
        elif event.held and event.hold_time > self.client.fps:
            base_char = menu_item.game_object.char
            if base_char:
                variants = self.char_variants.get(base_char, "")
                all_variants = base_char + variants
                choices = [
                    (c, c, partial(self.add_input_char_and_pop, c))
                    for c in all_variants
                ]
                self.client.push_state("ChoiceState", menu=choices)

    def _handle_backspace_event(self) -> None:
        self.backspace()

    def _handle_unicode_event(self, char: str) -> None:
        if char == " " or char in self.all_chars:
            self.add_input_char(char)
