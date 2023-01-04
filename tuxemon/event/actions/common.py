# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import logging

from tuxemon.npc import NPC

logger = logging.getLogger(__name__)

"""
[Core]
Name = Common
Module = Common

[Documentation]
Author = Adam Chevalier
Version = 1.0
Website = http://www.tuxemon.org
Description = Plugin containing utility functions common to multiple action plugins.
"""


class CommonAction:
    name = "Common"

    @staticmethod
    def set_character_attribute(
        character: NPC,
        attribute: str,
        value: str,
    ) -> None:
        """
        Set a character's (npc or player) attribute.

        Parameters:
            character: The NPC object to modify.
            attribute: The attribute to modify.
            value: The value to set the attribute to, as a string.

        """

        # check for valid inputs
        # trigger an AttributeError if the attribute doesn't already exist
        attr = None
        try:
            attr = getattr(character, attribute)
        except AttributeError:
            logger.warning(
                "Player attribute '{0}' specified does not exist.",
                attribute,
            )
            return

        try:
            val = type(attr)(value)
        except TypeError:
            logger.warning(
                "The value given cannot be parsed into the correct type for '{0}'",
                attribute,
            )
            return

        setattr(character, attribute, val)

    @staticmethod
    def modify_character_attribute(
        character: NPC,
        attribute: str,
        modifier: str,
    ) -> None:
        """
        Modify a character's (npc or player) attribute.

        Default behavior is to add the given mod to the attribute, but
        prepending a percent (%) symbol will cause the mod to be used
        as a multiplier.

        Parameters:
            character: The Player object to modify.
            attribute: The attribute to modify.
            modifier: The modifier to apply the attribute by.

        """

        # check for valid inputs
        # trigger an AttributeError if the attribute doesn't already exist
        try:
            attr = getattr(character, attribute)
        except AttributeError:
            logger.warning(
                "Player attribute '{0}' specified does not exist.",
                attribute,
            )
            return

        if "%" in modifier:
            attr *= float(modifier.replace("%", ""))
        else:
            attr += float(modifier)

        setattr(character, attribute, attr)
