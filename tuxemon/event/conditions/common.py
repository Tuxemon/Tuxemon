# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import logging
from typing import Any, Optional, Union

logger = logging.getLogger(__name__)
from tuxemon.db import Comparison
from tuxemon.tools import compare


class CommonCondition:
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
    def check_parameter(
        entity: object,
        parameter: str,
        value: str,
    ) -> bool:
        """
        Check a entity's parameter against a given value.

        Parameters:
            entity: The entity to check (NPC, Item, Technique, etc.).
            parameter: The entity's parameter (eg. "name", "steps", etc.)
            value: Given value to check against the parameter's value.

        eg. "player,name,alpha" -> is the player named alpha? true/false
        eg. "technique,power,2.0" -> is the technique power 2.0? true/false

        """
        attr = CommonCondition._get_attribute(entity, parameter)
        if attr is None:
            return False

        try:
            val = type(attr)(value)
        except TypeError:
            logger.warning(
                f"The value '{value}' given cannot be parsed into the correct type for '{parameter}'",
            )
            return False
        return attr == val  # type: ignore[no-any-return]

    @staticmethod
    def check_parameter_in(
        entity: object,
        parameter: str,
        values: str,
    ) -> bool:
        """
        Check if a entity's parameter is in a list of given values.

        Parameters:
            entity: The entity to check (NPC, Item, Technique, etc.).
            parameter: The entity's parameter (eg. "name", "steps", etc.)
            values: A ":"-separated list of values to check against the
                parameter's value.
        """
        attr = CommonCondition._get_attribute(entity, parameter)
        if attr is None:
            return False

        try:
            values_list = [type(attr)(value) for value in values.split(":")]
        except TypeError:
            logger.warning(
                f"The values '{values}' given cannot be parsed into the correct type for '{parameter}'",
            )
            return False
        return attr in values_list

    @staticmethod
    def check_parameter_in_dict(
        entity: object,
        parameter: str,
        key: str,
        value: str,
    ) -> bool:
        """
        Check if a entity's parameter is a dictionary and contains a key-value
        pair.

        Parameters:
            entity: The entity to check (NPC, Item, Technique, etc.).
            parameter: The entity's parameter (eg. "name", "steps", etc.)
            key: The key to check in the dictionary.
            value: The value to check against the key's value in the dictionary.
        """
        attr = CommonCondition._get_attribute(entity, parameter)
        if attr is None:
            return False

        if not isinstance(attr, dict):
            logger.warning(
                f"The parameter '{parameter}' is not a dictionary.",
            )
            return False

        key_value = attr.get(key)
        if key_value is None:
            logger.warning(
                f"The key '{key}' does not exist in the dictionary.",
            )
            return False

        try:
            value_to_check = type(key_value)(value)
        except TypeError:
            logger.warning(
                f"The value '{value}' given cannot be parsed into the correct type for '{key}'",
            )
            return False
        return key_value == value_to_check  # type: ignore[no-any-return]

    @staticmethod
    def check_parameter_in_list(
        entity: object,
        parameter: str,
        value: str,
    ) -> bool:
        """
        Check if a entity's parameter is a list and contains a value.

        Parameters:
            entity: The entity to check (NPC, Item, Technique, etc.).
            parameter: The entity's parameter (eg. "name", "steps", etc.)
            value: The value to check against the list.
        """

        attr = CommonCondition._get_attribute(entity, parameter)
        if attr is None:
            return False

        if not isinstance(attr, list):
            logger.warning(
                f"The parameter '{parameter}' is not a list.",
            )
            return False

        try:
            value_to_check = type(attr[0])(value)
        except TypeError:
            logger.warning(
                f"The value '{value}' given cannot be parsed into the correct type for '{parameter}'",
            )
            return False
        return value_to_check in attr

    @staticmethod
    def check_parameter_in_range(
        entity: object,
        parameter: str,
        min_value: str,
        max_value: str,
    ) -> bool:
        """
        Check if a entity's parameter is within a given range.

        Parameters:
            entity: The entity to check (NPC, Item, Technique, etc.).
            parameter: The entity's parameter (eg. "name", "steps", etc.)
            min_value: The minimum value of the range.
            max_value: The maximum value of the range.
        """

        attr = CommonCondition._get_attribute(entity, parameter)
        if attr is None:
            return False

        if not isinstance(attr, (int, float)):
            logger.warning(
                f"The parameter '{parameter}' is not a number, cannot check range",
            )
            return False

        try:
            min_val = type(attr)(min_value)
            max_val = type(attr)(max_value)
        except ValueError:
            logger.warning(
                f"The values '{min_value}' and '{max_value}' given cannot be parsed into the correct type for '{parameter}'",
            )
            return False

        if min_val > max_val:
            logger.warning(
                f"The minimum value '{min_value}' is greater than the maximum value '{max_value}' for '{parameter}'",
            )
            return False

        return min_val <= attr <= max_val

    @staticmethod
    def check_parameter_operator_value(
        entity: object,
        parameter: str,
        operator: str,
        value: Union[int, float],
    ) -> bool:
        """
        Check if a entity's parameter is greater_than, etc.

        Parameters:
            entity: The entity to check (NPC, Item, Technique, etc.).
            parameter: The entity's parameter (eg. "name", "steps", etc.)
            operator: Numeric comparison operator. Accepted values are "less_than",
                "less_or_equal", "greater_than", "greater_or_equal", "equals"
                and "not_equals".
            value: The value to check against the operator.
        """

        attr = CommonCondition._get_attribute(entity, parameter)
        if attr is None:
            return False

        if not isinstance(attr, (int, float)):
            logger.warning(
                f"The parameter '{parameter}' is not a number, cannot check range",
            )
            return False

        try:
            value_to_check = type(attr)(value)
        except ValueError:
            logger.warning(
                f"The value '{value}' given cannot be parsed into the correct type for '{parameter}'",
            )
            return False

        if operator not in list(Comparison):
            logger.warning(
                f"The operator '{operator}' given must be among '{list(Comparison)}'",
            )
            return False

        return compare(operator, value_to_check, value)
