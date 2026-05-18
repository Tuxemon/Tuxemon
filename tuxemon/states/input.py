# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Callable, Generator
from functools import partial
from typing import TYPE_CHECKING, Any, ClassVar

from pygame.rect import Rect

from tuxemon.locale.locale import T
from tuxemon.menu.input import (
    CharacterSetManager,
    InputController,
    NameDataLoader,
)
from tuxemon.menu.interface import MenuItem
from tuxemon.menu.menu import Menu
from tuxemon.platform.const import buttons, events, intentions
from tuxemon.session import local_session
from tuxemon.tools import open_choice_dialog
from tuxemon.ui.input_display import InputDisplay
from tuxemon.ui.menu_options import MenuOptions, create_choice_options

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.platform.events import PlayerInput


class InputMenuObj:
    def __init__(
        self,
        action: Callable[[], None],
        char: str | None = None,
    ):
        self.action = action
        self.char = char

    def __call__(self) -> None:
        return self.action()


class InputMenu(Menu[InputMenuObj]):
    """
    A menu interface used to input and edit text, featuring an on-screen
    character keyboard and configurable control buttons.

    Supports character limits, random name generation, character variant
    selection, and external button injection via plug-in functions.
    """

    name: ClassVar[str] = "InputMenu"
    background = None
    draw_borders = False

    def __init__(
        self,
        client: BaseClient,
        prompt: str = "",
        callback: Callable[[str], None] | None = None,
        initial: str = "",
        char_limit: int = 99,
        random: bool = False,
        button_injectors: None
        | (
            list[
                Callable[
                    [InputMenu], Generator[MenuItem[InputMenuObj], None, None]
                ]
            ]
        ) = None,
        char_manager: CharacterSetManager | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the input menu UI.

        Parameters:
            prompt: Optional label text to display above the input (e.g. "Name?").
            callback: Function to call with the final input string when confirmed.
            initial: Optional starting text value shown in the input field.
            char_limit: Maximum allowed number of input characters.
            random: Enables a "Don't Care" button for randomized name generation.
            button_injectors: Optional list of generator functions that inject
                additional MenuItem buttons into the layout.
            char_manager: Optional CharacterSetManager to control the active character
                set and variant mappings; falls back to defaults if not provided.
            **kwargs: Additional arguments passed to the base Menu.
        """
        self.button_injectors = button_injectors or []
        self._suppress_first_event = True
        self.name_loader = NameDataLoader("npc_names.yaml")
        self.input_controller = InputController(
            initial_string=initial, char_limit=char_limit
        )
        self.char_manager = char_manager or CharacterSetManager()

        self._repeat_timers: dict[int, float] = {
            buttons.UP: 0.0,
            buttons.DOWN: 0.0,
            buttons.LEFT: 0.0,
            buttons.RIGHT: 0.0,
        }
        super().__init__(client=client, **kwargs)

        # The following is necessary to prevent writing a char immediately
        # after leaving the char variant dialog.
        self.leaving_char_variant_dialog = False

        self.input_display = InputDisplay(
            context=self.client.context,
            font=self.font,
            font_color=self.font_color,
            prompt_text=prompt,
            initial_input_string=self.input_controller.current_string,
            area_rect=self.rect,
        )
        self.sprites.add(self.input_display.sprites)

        self.callback = callback
        self.char_limit = char_limit
        self.random = random
        assert self.callback

        self.update_char_counter()

    def calc_internal_rect(self) -> Rect:
        """Calculate the internal area of the menu for layout."""
        w = self.rect.width - self.rect.width * 0.95
        h = self.rect.height - self.rect.height * 0.5
        rect = self.rect.inflate(-w, -h)
        rect.top = int(self.rect.centery * 0.7)
        return rect

    def initialize_items(
        self,
    ) -> Generator[MenuItem[InputMenuObj], None, None]:
        """Generate keyboard and control buttons, including optional external injectors."""
        self.menu_items.columns = max(
            1, self.rect.width // int(self.rect.width * 0.075)
        )
        layout = self.char_manager.get_layout_grid(self.menu_items.columns)

        for row in layout:
            for char in row:
                if char is None:
                    yield self._create_empty_item()
                else:
                    yield self._create_char_item(char)

        yield from self.generate_default_buttons()

        for injector in self.button_injectors:
            yield from injector(self)

    def generate_default_buttons(
        self,
    ) -> Generator[MenuItem[InputMenuObj], None, None]:
        """Yield the core control buttons for the input menu."""
        yield MenuItem(
            self.shadow_text("←"),
            None,
            None,
            InputMenuObj(self.backspace),
        )

        yield MenuItem(
            self.shadow_text("END"),
            None,
            None,
            InputMenuObj(self.confirm),
        )

        if self.random:
            yield MenuItem(
                self.shadow_text(T.translate("random").upper()),
                None,
                None,
                InputMenuObj(self.pick_random),
            )

    def process_event(self, event: PlayerInput) -> PlayerInput | None:
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
        """Handler for empty character slots (no action)."""

    def backspace(self) -> None:
        """Remove the last character from the input string."""
        self.input_controller.backspace()
        self.update_text_area()
        self.update_char_counter()

    def add_input_char_and_pop(self, char: str) -> None:
        """Add character from variant dialog and close the variant menu."""
        self.leaving_char_variant_dialog = True
        self.input_controller.add_char(char)
        self.update_text_area()
        self.update_char_counter()
        self.client.pop_state()

    def add_input_char(self, char: str) -> None:
        """Add character to input string or show alert if limit exceeded."""
        if self._suppress_first_event:
            self._suppress_first_event = False
            return

        if self.input_controller.add_char(char):
            self.update_text_area()
            self.update_char_counter()
        else:
            self.input_display.update_input_string(T.translate("alert_text"))

    def update_text_area(self) -> None:
        """Update the text area to reflect the current input string."""
        self.input_display.update_input_string(
            self.input_controller.current_string
        )

    def update_char_counter(self) -> None:
        """Update the character count display."""
        self.input_display.update_char_counter(
            self.input_controller.remaining_chars
        )

    def confirm(self) -> None:
        """Trigger the input confirmation and invoke callback."""
        final_input_string = self.input_controller.current_string
        if not final_input_string and self.char_limit > 0:
            return
        if self.callback is None:
            raise ValueError("Callback function not provided!")
        self.callback(final_input_string)
        self.client.pop_state(self)

    def pick_random(self) -> None:
        """Assign a random name based on gender and language preferences."""
        gender = local_session.player.gender or "neutral"
        language = T.get_current_language().lower()
        fallback_language = self.client.config.locale.slug.lower()
        random_name = self.name_loader.get_random_name(
            gender, language, fallback_language
        )
        self.input_controller.set_string(random_name)
        self.update_text_area()
        self.update_char_counter()

    def _create_empty_item(self) -> MenuItem[InputMenuObj]:
        """Create a disabled menu item representing an empty key."""
        empty = MenuItem(
            self.shadow_text(" "),
            None,
            None,
            InputMenuObj(self.empty),
        )
        empty.enabled = False
        return empty

    def _create_char_item(self, char: str) -> MenuItem[InputMenuObj]:
        """Create a character key menu item."""
        return MenuItem(
            self.shadow_text(char),
            None,
            None,
            InputMenuObj(partial(self.add_input_char, char), char),
        )

    def _handle_select_event(self, event: PlayerInput) -> None:
        """Handle selection input on a menu item."""
        menu_item = self.get_selected_item()
        if menu_item is None:
            return

        if event.triggered:
            if self.leaving_char_variant_dialog:
                self.leaving_char_variant_dialog = False
                if menu_item.game_object.char:
                    self.input_controller.add_char(menu_item.game_object.char)
                    self.update_text_area()
                    self.update_char_counter()
            else:
                menu_item.game_object()

        elif event.held and event.hold_time > self.client.config.fps:
            base_char = menu_item.game_object.char
            if base_char:
                variants = self.char_manager.get_char_variants(base_char)
                all_variants = [base_char] + list(variants)

                actions = {
                    c: partial(self.add_input_char_and_pop, c)
                    for c in all_variants
                }
                options = create_choice_options(actions)

                menu = MenuOptions(options)
                open_choice_dialog(client=self.client, menu=menu)

    def _handle_backspace_event(self) -> None:
        """Handle the backspace key event."""
        self.backspace()

    def _handle_unicode_event(self, char: str) -> None:
        """Handle unicode character input event."""
        if self.char_manager.is_valid_input_char(char):
            self.add_input_char(char)
