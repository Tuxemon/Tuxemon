# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random as rd
from collections.abc import Callable, Generator
from functools import partial
from typing import Any, ClassVar, Optional

import yaml
from pygame.rect import Rect

from tuxemon.constants import paths
from tuxemon.locale import T
from tuxemon.menu.interface import MenuItem
from tuxemon.menu.menu import Menu
from tuxemon.platform.const import buttons, events, intentions
from tuxemon.platform.events import PlayerInput
from tuxemon.session import local_session
from tuxemon.tools import open_choice_dialog
from tuxemon.ui.input_display import InputDisplay
from tuxemon.ui.menu_options import ChoiceOption, MenuOptions


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


class NameDataLoader:
    """
    Handles loading of NPC names and providing random names.
    """

    def __init__(self, file_path: str) -> None:
        self._name_data: dict[str, Any] = self._load_names(file_path)

    def _load_names(self, file_path: str) -> Any:
        """Loads name data from a YAML file."""
        yaml_path = paths.mods_folder / file_path
        with yaml_path.open() as file:
            return yaml.safe_load(file)

    def get_random_name(
        self, gender: str, language: str, fallback_language: str
    ) -> str:
        """
        Retrieves a random name based on gender and language.

        Parameters:
            gender: The desired gender for the name (e.g., "male", "female", "neutral").
            language: The primary language slug (e.g., "en", "es").
            fallback_language: A fallback language slug if the primary language is not found.

        Returns:
            A random name string.

        Raises:
            ValueError: If names are not found for the given language/gender
                        or fallback language/gender combination.
        """
        if gender not in ["male", "female", "neutral"]:
            gender = "neutral"

        try:
            name = rd.choice(self._name_data["random_names"][language][gender])
        except (KeyError, IndexError):
            try:
                name = rd.choice(
                    self._name_data["random_names"][fallback_language][gender]
                )
            except (KeyError, IndexError) as e:
                raise ValueError(
                    f"Names not found for language '{language}' "
                    f"or fallback language '{fallback_language}' and gender '{gender}'."
                ) from e
        return str(name)


class CharacterSetManager:
    """
    Manages the available characters for input menus and their variants,
    loading data from localization strings.
    """

    def __init__(
        self,
        chars: Optional[str] = None,
        char_variants: Optional[str] = None,
    ) -> None:
        _chars = chars or T.translate("menu_alphabet")
        self.chars = (_chars or "").replace(r"\0", "\0")
        _char_variants = char_variants or T.translate("menu_char_variants")
        self.char_variants = self._parse_char_variants(_char_variants)
        self.all_chars = self.chars + "".join(self.char_variants.values())

    def _parse_char_variants(self, variant_string: str) -> dict[str, str]:
        """
        Parses the multi-line character variant string into a dictionary.
        Skips parsing if the string is missing or appears to be an untranslated key.
        """
        variants_dict: dict[str, str] = {}
        if not variant_string or "menu_char_variants" in variant_string:
            return variants_dict

        for line in variant_string.split("\n"):
            if line:
                base_char = line[0]
                other_variants = line[1:]
                variants_dict[base_char] = other_variants
        return variants_dict

    def get_char_variants(self, base_char: str) -> str:
        """
        Returns a string of variants for a given base character.
        Returns an empty string if no variants exist.
        """
        return self.char_variants.get(base_char, "")

    def is_valid_input_char(self, char: str) -> bool:
        """Checks if a character is part of the main alphabet or a known variant."""
        return char in self.all_chars or char == " "

    def get_layout_grid(self, columns: int) -> list[list[Optional[str]]]:
        """
        Returns the characters arranged in a grid with given columns.
        Empty cells (from '\0') are represented as None.
        """
        grid: list[list[Optional[str]]] = []
        row: list[Optional[str]] = []

        for char in self.all_chars:
            if char == "\0":
                row.append(None)
            else:
                row.append(char)

            if len(row) == columns:
                grid.append(row)
                row = []

        if row:
            grid.append(row)

        return grid


class InputController:
    """
    Manages a text input field with character limit enforcement,
    supporting appending, backspace, resetting, and direct overrides.
    """

    def __init__(self, initial_string: str = "", char_limit: int = 99) -> None:
        self._initial_string: str = initial_string
        self._input_string: str = initial_string
        self._char_limit: int = char_limit

    @property
    def current_string(self) -> str:
        """Return the current value of the input string."""
        return self._input_string

    @property
    def remaining_chars(self) -> int:
        """Return the number of characters that can still be added."""
        return max(0, self._char_limit - len(self._input_string))

    @property
    def initial_string(self) -> str:
        """Return the original string passed at initialization."""
        return self._initial_string

    @property
    def char_limit(self) -> int:
        """Return the maximum number of allowed characters."""
        return self._char_limit

    def add_char(self, char: str) -> bool:
        """
        Append a character to the current string, if within the limit.

        Returns True if the character was added, False if limit was reached.
        """
        if (
            self._char_limit is None
            or len(self._input_string) < self._char_limit
        ):
            self._input_string += char
            return True

        return False

    def backspace(self) -> None:
        """Remove the last character from the string; revert to empty if cleared."""
        if self._input_string:
            self._input_string = self._input_string[:-1]
            if not self._input_string:
                self._input_string = ""

    def set_string(self, new_string: str) -> None:
        """Set the entire string directly, truncating if necessary to fit the limit."""
        if len(new_string) <= self._char_limit:
            self._input_string = new_string
        else:
            self._input_string = new_string[: self._char_limit]

    def clear(self) -> None:
        """Reset the input string to the original initial string."""
        self._input_string = self._initial_string


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
        prompt: str = "",
        callback: Optional[Callable[[str], None]] = None,
        initial: str = "",
        char_limit: int = 99,
        random: bool = False,
        button_injectors: Optional[
            list[
                Callable[
                    [InputMenu], Generator[MenuItem[InputMenuObj], None, None]
                ]
            ]
        ] = None,
        char_manager: Optional[CharacterSetManager] = None,
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

        super().__init__(**kwargs)

        # The following is necessary to prevent writing a char immediately
        # after leaving the char variant dialog.
        self.leaving_char_variant_dialog = False

        self.input_display = InputDisplay(
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
                self.shadow_text(T.translate("dont_care")),
                None,
                None,
                InputMenuObj(self.dont_care),
            )

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        """Process player input and dispatch to appropriate handlers."""
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

    def dont_care(self) -> None:
        """Assign a random name based on gender and language preferences."""
        variables = local_session.player.game_variables
        gender = variables.get("gender_choice", "neutral")
        if gender not in ["male", "female"]:
            gender = "neutral"
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
                all_variants = base_char + variants

                options = [
                    ChoiceOption(
                        key=c,
                        display_text=c,
                        action=partial(self.add_input_char_and_pop, c),
                    )
                    for c in all_variants
                ]

                menu = MenuOptions(options)
                open_choice_dialog(client=self.client, menu=menu)

    def _handle_backspace_event(self) -> None:
        """Handle the backspace key event."""
        self.backspace()

    def _handle_unicode_event(self, char: str) -> None:
        """Handle unicode character input event."""
        if self.char_manager.is_valid_input_char(char):
            self.add_input_char(char)
