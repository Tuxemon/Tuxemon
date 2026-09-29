# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from tuxemon.locale.locale import T


def noop_action() -> None:
    """A no-op placeholder action."""


@dataclass
class ChoiceOption:
    """Represents a single option in a choice dialog."""

    key: str = ""
    display_text: str = ""
    action: Callable[[], None] = field(default_factory=lambda: noop_action)

    def __post_init__(self) -> None:
        self.key = self.key.lower().strip()

        if not self.display_text:
            self.display_text = f"Option {self.key or 'Unnamed'}"


class MenuOptions:
    """Manages a collection of ChoiceOption entries for a menu dialog."""

    def __init__(self, options: Sequence[ChoiceOption]) -> None:
        """Initializes the menu with a sequence of choice options."""
        self.options = list(options)

    def add(self, option: ChoiceOption, position: int | None = None) -> None:
        """Adds a new option to the menu, optionally at a specific index."""
        if position is None:
            self.options.append(option)
        else:
            self.options.insert(position, option)

    def remove(self, key: str) -> None:
        """Removes the option with the specified key from the menu."""
        self.options = [opt for opt in self.options if opt.key != key]

    def replace(self, key: str, new_option: ChoiceOption) -> None:
        """Replaces an option with the given key using a new option."""
        for i, opt in enumerate(self.options):
            if opt.key == key:
                self.options[i] = new_option
                break

    def get_menu(self) -> Sequence[ChoiceOption]:
        """Returns the current list of menu options."""
        return self.options

    def remove_by_condition(
        self, condition: Callable[[ChoiceOption], bool]
    ) -> None:
        """Removes all options that satisfy the provided condition function."""
        self.options = [opt for opt in self.options if not condition(opt)]

    def add_or_replace(self, new_option: ChoiceOption) -> None:
        """Adds the new option, or replaces the existing one if the key matches."""
        for i, opt in enumerate(self.options):
            if opt.key == new_option.key:
                self.options[i] = new_option
                return
        self.options.append(new_option)

    def sort(
        self,
        key_function: Callable[[ChoiceOption], Any],
        reverse: bool = False,
    ) -> None:
        """Sorts the menu options using the provided key function."""
        self.options.sort(key=key_function, reverse=reverse)

    def filter(self, condition: Callable[[ChoiceOption], bool]) -> None:
        """Keeps only the options that match the condition function."""
        self.options = [opt for opt in self.options if condition(opt)]

    def group_by_prefix(self, prefix: str) -> list[ChoiceOption]:
        """Returns options whose keys start with the given prefix."""
        return [opt for opt in self.options if opt.key.startswith(prefix)]

    def disable(self, key: str) -> None:
        """Disables the option with the given key by replacing its action with no-op."""
        for opt in self.options:
            if opt.key == key:
                opt.action = noop_action
                break


def create_choice_options(
    actions: Mapping[str, Callable[..., None]],
) -> list[ChoiceOption]:
    """
    Creates a list of ChoiceOption objects from a dictionary of choice keys and
    actions.

    The keys in the dictionary should map to translation keys
    (e.g., 'no' -> T.translate('no')).
    The list is generated in the order of the dictionary keys.

    Parameters:
        actions: A dictionary mapping choice keys (e.g., "yes", "no") to their
            action callables.

    Returns:
        A list of ChoiceOption objects.
    """
    options: list[ChoiceOption] = []
    for key, action in actions.items():
        options.append(
            ChoiceOption(
                key=key,
                display_text=T.translate(key).upper(),
                action=action,
            )
        )
    return options


def create_yes_no_options(
    yes_action: Callable[..., None],
    no_action: Callable[..., None],
    reverse_order: bool = False,
) -> list[ChoiceOption]:
    """
    Specialized utility for Yes/No, often displayed as [NO, YES].
    """
    actions: dict[str, Callable[..., None]] = {
        "no": no_action,
        "yes": yes_action,
    }
    ordered_actions = (
        actions if not reverse_order else {"yes": yes_action, "no": no_action}
    )
    return create_choice_options(ordered_actions)
