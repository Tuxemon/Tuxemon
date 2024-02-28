# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import logging
from typing import Union

from tuxemon.monster import Monster
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
    def set_entity_attribute(
        entity: Union[NPC, Monster],
        attribute: str,
        value: str,
    ) -> None:
        """
        Set an entity's (npc or player or monster) attribute.

        Parameters:
            entity: The NPC/Monster object to modify.
            attribute: The attribute to modify.
            value: The value to set the attribute to, as a string.

        """

        # check for valid inputs
        # trigger an AttributeError if the attribute doesn't already exist
        attr = None
        try:
            attr = getattr(entity, attribute)
        except AttributeError:
            logger.warning(
                "Entity attribute '{0}' specified does not exist.",
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

        setattr(entity, attribute, val)

    @staticmethod
    def modify_entity_attribute(
        entity: Union[NPC, Monster],
        attribute: str,
        modifier: str,
    ) -> None:
        """
        Modify an entity's (npc or player or monster) attribute.

        Default behavior is to add the given mod to the attribute, but
        prepending a percent (%) symbol will cause the mod to be used
        as a multiplier.

        Parameters:
            entity: The NPC/Monster object to modify.
            attribute: The attribute to modify.
            modifier: The modifier to apply the attribute by.

        """

        # check for valid inputs
        # trigger an AttributeError if the attribute doesn't already exist
        try:
            attr = getattr(entity, attribute)
        except AttributeError:
            logger.warning(
                "Entity attribute '{0}' specified does not exist.",
                attribute,
            )
            return

        if "%" in modifier:
            attr *= float(modifier.replace("%", ""))
        else:
            attr += float(modifier)

        setattr(entity, attribute, attr)
