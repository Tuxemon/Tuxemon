# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import logging

from tuxemon.npc import NPC

logger = logging.getLogger(__name__)


class CommonCondition:
    name = "Common"

    @staticmethod
    def check_character_parameter(
        character: NPC,
        parameter: str,
        value: str,
    ) -> bool:
        """
        Check a character's parameter against a given value.

        Parameters:
            character: The character to check.
            parameter: The character's parameter (eg. "name", "steps", etc.)
            value: Given value to check against the parameter's value.

        eg. "player,name,alpha" -> is the player named alpha? true/false

        """

        # check for valid inputs
        # trigger an AttributeError if the parameter doesn't already exist
        attr = None
        try:
            attr = getattr(character, parameter)
        except AttributeError:
            logger.warning(
                "Character parameter '{0}' specified does not exist.",
                parameter,
            )
            return False

        try:
            val = type(attr)(value)
        except TypeError:
            logger.warning(
                "The value given cannot be parsed into the correct type for '{0}'",
                parameter,
            )
            return False
        return attr == val  # type: ignore[no-any-return]
