# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import logging
from typing import Any, Optional

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
    def _get_attribute(entity: object, parameter: str) -> Optional[Any]:
        """
        Get the attribute of an entity.

        Returns:
            The attribute value if it exists, otherwise None.
        """
        try:
            return getattr(entity, parameter)
        except AttributeError:
            logger.warning(
                f"Entity parameter '{parameter}' specified does not exist.",
            )
            return None

    @staticmethod
    def set_entity_attribute(
        entity: object,
        parameter: str,
        value: str,
    ) -> None:
        """
        Set an entity's (npc or player or monster) parameter.

        Parameters:
            entity: The entity object to modify.
            parameter: The parameter to modify.
            value: The value to set the parameter to, as a string.

        """
        attr = CommonAction._get_attribute(entity, parameter)
        if attr is None:
            return

        try:
            val = type(attr)(value)
        except (TypeError, ValueError):
            logger.warning(
                f"The value given cannot be parsed into the correct type for '{parameter}'",
            )
            return

        setattr(entity, parameter, val)

    @staticmethod
    def modify_entity_attribute(
        entity: object,
        parameter: str,
        modifier: str,
    ) -> None:
        """
        Modify an entity's (npc or player or monster) parameter.

        Default behavior is to add the given mod to the parameter, but
        prepending a percent (%) symbol will cause the mod to be used
        as a multiplier.

        Parameters:
            entity: The entity object to modify.
            parameter: The parameter to modify.
            modifier: The modifier to apply the parameter by.

        """
        attr = CommonAction._get_attribute(entity, parameter)
        if attr is None:
            return

        if not isinstance(attr, (int, float)):
            logger.warning(
                f"Cannot modify non-numeric attribute '{parameter}'",
            )
            return

        try:
            if "%" in modifier:
                new_attr = attr * float(modifier.replace("%", ""))
            else:
                new_attr = attr + float(modifier)
        except ValueError:
            logger.warning(
                f"Invalid modifier '{modifier}' for attribute '{parameter}'",
            )
            return

        setattr(entity, parameter, new_attr)

    @staticmethod
    def get_list_attribute(
        entity: object, parameter: str, index: int
    ) -> Optional[Any]:
        """
        Get an attribute from a list.

        Parameters:
            entity: The entity object to get the attribute from.
            parameter: The name of the list attribute.
            index: The index of the attribute to get.

        Returns:
            The attribute value if it exists, otherwise None.
        """
        attr = CommonAction._get_attribute(entity, parameter)
        if attr is None:
            return None

        if not isinstance(attr, list):
            logger.warning(
                f"Attribute '{parameter}' is not a list",
            )
            return None

        if index < 0 or index >= len(attr):
            logger.warning(
                f"Index {index} is out of range for attribute '{parameter}'",
            )
            return None

        return attr[index]

    @staticmethod
    def set_list_attribute(
        entity: object, parameter: str, index: int, value: Any
    ) -> None:
        """
        Set an attribute in a list.

        Parameters:
            entity: The entity object to set the attribute in.
            parameter: The name of the list attribute.
            index: The index of the attribute to set.
            value: The value to set the attribute to.
        """
        attr = CommonAction._get_attribute(entity, parameter)
        if attr is None:
            return

        if not isinstance(attr, list):
            logger.warning(
                f"Attribute '{parameter}' is not a list",
            )
            return

        if index < 0 or index >= len(attr):
            logger.warning(
                f"Index {index} is out of range for attribute '{parameter}'",
            )
            return

        attr[index] = value
        setattr(entity, parameter, attr)

    @staticmethod
    def get_dict_attribute(
        entity: object, parameter: str, key: str
    ) -> Optional[Any]:
        """
        Get an attribute from a dictionary.

        Parameters:
            entity: The entity object to get the attribute from.
            parameter: The name of the dictionary attribute.
            key: The key of the attribute to get.

        Returns:
            The attribute value if it exists, otherwise None.
        """
        attr = CommonAction._get_attribute(entity, parameter)
        if attr is None:
            return None

        if not isinstance(attr, dict):
            logger.warning(
                f"Attribute '{parameter}' is not a dictionary",
            )
            return None

        return attr.get(key)

    @staticmethod
    def set_dict_attribute(
        entity: object, parameter: str, key: str, value: Any
    ) -> None:
        """
        Set an attribute in a dictionary.

        Parameters:
            entity: The entity object to set the attribute in.
            parameter: The name of the dictionary attribute.
            key: The key of the attribute to set.
            value: The value to set the attribute to.
        """
        attr = CommonAction._get_attribute(entity, parameter)
        if attr is None:
            return

        if not isinstance(attr, dict):
            logger.warning(
                f"Attribute '{parameter}' is not a dictionary",
            )
            return

        attr[key] = value
        setattr(entity, parameter, attr)

    @staticmethod
    def append_to_list_attribute(
        entity: object, parameter: str, value: Any
    ) -> None:
        """
        Append a value to a list attribute.

        Parameters:
            entity: The entity object to append the value to.
            parameter: The name of the list attribute.
            value: The value to append.
        """
        attr = CommonAction._get_attribute(entity, parameter)
        if attr is None:
            return

        if not isinstance(attr, list):
            logger.warning(
                f"Attribute '{parameter}' is not a list",
            )
            return

        attr.append(value)
        setattr(entity, parameter, attr)

    @staticmethod
    def add_to_dict_attribute(
        entity: object, parameter: str, key: str, value: Any
    ) -> None:
        """
        Add a key-value pair to a dictionary attribute.

        Parameters:
            entity: The entity object to add the key-value pair to.
            parameter: The name of the dictionary attribute.
            key: The key to add.
            value: The value to add.
        """
        attr = CommonAction._get_attribute(entity, parameter)
        if attr is None:
            return

        if not isinstance(attr, dict):
            logger.warning(
                f"Attribute '{parameter}' is not a dictionary",
            )
            return

        attr[key] = value
        setattr(entity, parameter, attr)
