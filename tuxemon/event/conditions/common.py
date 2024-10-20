# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import logging

logger = logging.getLogger(__name__)


class CommonCondition:
    name = "Common"

    @staticmethod
    def check_parameter(
        entity: object,
        parameter: str,
        value: str,
    ) -> bool:
        """
        Check a entity's parameter against a given value.

        Parameters:
            entity: The entity to check (NPC, Item, Technique, etc.).
            parameter: The character's parameter (eg. "name", "steps", etc.)
            value: Given value to check against the parameter's value.

        eg. "player,name,alpha" -> is the player named alpha? true/false
        eg. "technique,power,2.0" -> is the technique power 2.0? true/false

        """

        # check for valid inputs
        # trigger an AttributeError if the parameter doesn't already exist
        attr = None
        try:
            attr = getattr(entity, parameter)
        except AttributeError:
            logger.warning(
                f"Entity parameter '{parameter}' specified does not exist.",
            )
            return False

        try:
            val = type(attr)(value)
        except TypeError:
            logger.warning(
                f"The value '{value}' given cannot be parsed into the correct type for '{parameter}'",
            )
            return False
        return attr == val  # type: ignore[no-any-return]
