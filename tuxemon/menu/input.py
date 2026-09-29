# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from typing import Any

from tuxemon.constants import paths
from tuxemon.database.yaml_utils import load_yaml
from tuxemon.locale.locale import T


class NameDataLoader:
    """
    Handles loading of NPC names and providing random names.
    """

    def __init__(self, file_path: str) -> None:
        self._name_data: dict[str, Any] = self._load_names(file_path)

    def _load_names(self, file_path: str) -> Any:
        """Loads name data from a YAML file."""
        yaml_path = paths.mods_folder / file_path
        return load_yaml(yaml_path)

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
            name = random.choice(
                self._name_data["random_names"][language][gender]
            )
        except (KeyError, IndexError):
            try:
                name = random.choice(
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
        chars: str | None = None,
        char_variants: str | None = None,
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

    def get_layout_grid(self, columns: int) -> list[list[str | None]]:
        """
        Returns the characters arranged in a grid with given columns.
        Empty cells (from '\0') are represented as None.
        """
        grid: list[list[str | None]] = []
        row: list[str | None] = []

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
