# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Callable, Mapping, Sequence
from functools import partial
from typing import Optional

from tuxemon import prepare
from tuxemon.formula import convert_ft, convert_km, convert_lbs, convert_mi
from tuxemon.locale import TranslatorManager
from tuxemon.menu.formatter import CurrencyFormatter
from tuxemon.session import Session
from tuxemon.ui.cipher_processor import CipherProcessor
from tuxemon.ui.text_paginator import TextPaginator

logger = logging.getLogger(__name__)


class TextFormatter:
    """
    A class responsible for formatting text by replacing placeholders with
    dynamic values.
    """

    def __init__(
        self,
        session: Session,
        translator: TranslatorManager,
        cipher_processor: Optional[CipherProcessor] = None,
        paginator: Optional[TextPaginator] = None,
    ):
        self.session = session
        self.translator = translator
        self.paginator = paginator or TextPaginator()
        self.cipher_processor = cipher_processor
        self._replacements: dict[str, Callable[[], str]] = {}
        self._register_default_replacements()

    @classmethod
    def replace_text(
        cls,
        session: Session,
        text: str,
        translator: TranslatorManager,
        cipher_processor: Optional[CipherProcessor] = None,
        paginator: Optional[TextPaginator] = None,
    ) -> str:
        """
        Convenience class method to format text without instantiating the formatter directly.
        """
        formatter = cls(session, translator, cipher_processor, paginator)
        return formatter.format_text(text)

    def set_paginator(self, paginator: TextPaginator) -> None:
        """Replaces the current paginator with a new one."""
        self.paginator = paginator

    def _register_player_client_replacements(self) -> None:
        """Registers replacements related to the player and client."""
        player = self.session.player
        client = self.session.client
        formatter = CurrencyFormatter()

        player_client_map = {
            "${{name}}": lambda: player.name,
            "${{NAME}}": lambda: player.name.upper(),
            "${{currency}}": lambda: "$",
            "${{money}}": lambda: str(
                player.money_controller.money_manager.get_money()
            ),
            "${{money_formatted}}": lambda: formatter.format(
                player.money_controller.money_manager.get_money()
            ),
            "${{tuxepedia_seen}}": lambda: str(
                player.tuxepedia.get_seen_count()
            ),
            "${{tuxepedia_caught}}": lambda: str(
                player.tuxepedia.get_caught_count()
            ),
            "${{map_name}}": lambda: client.map_manager.map_name,
            "${{map_desc}}": lambda: client.map_manager.map_desc,
            "${{north}}": lambda: client.map_manager.map_north,
            "${{south}}": lambda: client.map_manager.map_south,
            "${{east}}": lambda: client.map_manager.map_east,
            "${{west}}": lambda: client.map_manager.map_west,
        }
        for placeholder, callable_func in player_client_map.items():
            self.register_replacement(placeholder, callable_func)

    def _register_unit_measure_replacements(self) -> None:
        """Registers replacements for units of measurement (metric vs. imperial)."""
        player = self.session.player
        unit_measure = prepare.CONFIG.unit_measure

        unit_map = {}
        if unit_measure == "metric":
            unit_map["${{length}}"] = lambda: prepare.U_KM
            unit_map["${{weight}}"] = lambda: prepare.U_KG
            unit_map["${{height}}"] = lambda: prepare.U_CM
            unit_map["${{steps}}"] = lambda: str(convert_km(player.steps))
        else:  # Assuming "imperial" for non-metric
            unit_map["${{length}}"] = lambda: prepare.U_MI
            unit_map["${{weight}}"] = lambda: prepare.U_LB
            unit_map["${{height}}"] = lambda: prepare.U_FT
            unit_map["${{steps}}"] = lambda: str(convert_mi(player.steps))

        for placeholder, callable_func in unit_map.items():
            self.register_replacement(placeholder, callable_func)

    def _register_monster_replacements(self) -> None:
        """Registers replacements for each monster in the player's party."""
        player = self.session.player
        unit_measure = prepare.CONFIG.unit_measure

        # Define common monster attributes and their callables
        monster_attributes = {
            "name": lambda m: m.name,
            "desc": lambda m: m.description,
            "category": lambda m: m.category,
            "hp": lambda m: str(m.current_hp),
            "hp_max": lambda m: str(m.hp),
            "level": lambda m: str(m.level),
            "bond": lambda m: str(m.bond),
            "txmn_id": lambda m: str(m.txmn_id),
            "armour": lambda m: str(m.armour),
            "dodge": lambda m: str(m.dodge),
            "melee": lambda m: str(m.melee),
            "ranged": lambda m: str(m.ranged),
            "speed": lambda m: str(m.speed),
            "types": lambda m: " - ".join(
                self.translator.translate(_type.name)
                for _type in m.types.current
            ),
            "shape": lambda m: self.translator.translate(m.shape.slug),
            "gender": lambda m: self.translator.translate(
                f"gender_{m.gender}"
            ),
            "warm": lambda m: self.translator.translate(
                f"taste_{m.taste_warm}"
            ),
            "cold": lambda m: self.translator.translate(
                f"taste_{m.taste_cold}"
            ),
            "moves": lambda m: " - ".join(
                _move.name for _move in m.moves.get_moves()
            ),
        }

        # Define unit-dependent monster attributes
        unit_dependent_monster_attributes = {
            "metric": {
                "steps": lambda m: str(convert_km(m.steps)),
                "weight": lambda m: str(m.weight),
                "height": lambda m: str(m.height),
            },
            "imperial": {
                "steps": lambda m: str(convert_mi(m.steps)),
                "weight": lambda m: str(convert_lbs(m.weight)),
                "height": lambda m: str(convert_ft(m.height)),
            },
        }

        for i, monster in enumerate(player.monsters):
            # Register common attributes
            for key, func in monster_attributes.items():
                self.register_replacement(
                    f"${{monster_{i}_{key}}}", partial(func, monster)
                )

            # Register unit-dependent attributes
            unit_key = "metric" if unit_measure == "metric" else "imperial"
            for key, func in unit_dependent_monster_attributes[
                unit_key
            ].items():
                self.register_replacement(
                    f"${{monster_{i}_{key}}}", partial(func, monster)
                )

    def _register_game_variable_replacements(self) -> None:
        """Registers replacements for game-specific variables."""
        player = self.session.player
        for key, value in player.game_variables.items():
            self.register_replacement(f"${{var:{key}}}", partial(str, value))
            self.register_replacement(
                f"${{msgid:{key}}}",
                partial(self.translator.translate, str(value)),
            )

    def _register_default_replacements(self) -> None:
        """Registers the common, built-in replacements by calling helper methods."""
        self._register_player_client_replacements()
        self._register_unit_measure_replacements()
        self._register_monster_replacements()
        self._register_game_variable_replacements()

    def register_replacement(
        self, placeholder: str, value_callable: Callable[[], str]
    ) -> None:
        """
        Registers a custom replacement.

        Parameters:
            placeholder: The placeholder string (e.g., "${{custom_var}}").
            value_callable: A callable (function or lambda) that returns the
                string value for the placeholder. This allows for dynamic
                retrieval of values at the time of formatting.
        """
        if (
            not isinstance(placeholder, str)
            or not placeholder.startswith("${{")
            or not placeholder.endswith("}}")
        ):
            logger.warning(
                f"Registering non-standard placeholder format: {placeholder}"
            )
        self._replacements[placeholder] = value_callable
        logger.debug(f"Registered replacement: {placeholder}")

    def unregister_replacement(self, placeholder: str) -> None:
        """
        Unregisters a replacement if it exists.

        Parameters:
            placeholder: The placeholder string to unregister.
        """
        if placeholder in self._replacements:
            del self._replacements[placeholder]
            logger.info(f"Unregistered placeholder: {placeholder}")
        else:
            logger.warning(
                f"Attempted to unregister non-existent placeholder: {placeholder}"
            )

    def clear_replacements(self) -> None:
        """
        Clears all registered replacements.
        """
        self._replacements.clear()
        logger.info("All TextFormatter replacements cleared.")

    def format_text(self, text: str) -> str:
        """
        Replaces variables in a text string with their dynamic values.

        Parameters:
            text: Text whose references to variables should be substituted.

        Returns:
            The formatted string.
        """
        formatted_text = text.replace(r"\n", "\n")
        temp_text = formatted_text

        # Evaluate callables and perform replacements
        for placeholder, value_callable in self._replacements.items():
            if placeholder in temp_text:
                try:
                    replacement_value = value_callable()
                    temp_text = temp_text.replace(
                        placeholder, replacement_value
                    )
                except Exception as e:
                    logger.error(
                        f"Error evaluating replacement for placeholder '{placeholder}': {e}",
                        exc_info=True,
                    )
                    temp_text = temp_text.replace(
                        placeholder, f"[ERROR:{placeholder}]"
                    )
            formatted_text = temp_text

        # Check for any remaining placeholder patterns that were not registered
        import re

        # Find all occurrences of ${{...}} pattern
        remaining_placeholder_patterns = re.findall(
            r"\$\{\{.*?\}\}", formatted_text
        )
        for placeholder in remaining_placeholder_patterns:
            if placeholder not in self._replacements:
                logger.warning(
                    f"Unhandled placeholder '{placeholder}' found in text after formatting. "
                    "Consider registering it or checking for typos."
                )

        if self.cipher_processor:
            formatted_text = self.cipher_processor.apply_cipher(formatted_text)

        return formatted_text

    def paginate_translation(
        self,
        text_slug: str,
        parameters: Optional[Mapping[str, str]] = None,
    ) -> Sequence[str]:
        """
        Translates a dialog and processes it into a sequence of pages of text,
        applying dynamic replacements.

        Parameters:
            text_slug: The translation slug for the main text.
            parameters: A dictionary of key-value pairs for additional formatting
                within the translated string (e.g., {"item_name": "Potion"}).
                These parameters are applied *after* the initial dynamic replacements.

        Returns:
            A sequence of formatted text pages.
        """
        # Use the injected translator for checking and formatting
        self.translator.check_translation(text_slug)
        translated_text = self.translator.format(text_slug, parameters)

        # Apply general dynamic replacements from TextFormatter
        processed_text = self.format_text(translated_text)

        # Use the injected paginator to split the text into pages
        pages = self.paginator.paginate_text(processed_text)

        # Apply format_text to each page again. This is primarily useful if:
        # 1. Placeholders could span across the original newline characters
        #  (which they shouldn't with ${{...}})
        # 2. Contextual replacements might change based on the isolated page content
        #  (unlikely for this design)
        # For this design, if format_text on the whole string is complete, this loop
        # might be redundant but is kept for safety or if future placeholder types
        # could introduce newlines.
        return [self.format_text(page) for page in pages]
