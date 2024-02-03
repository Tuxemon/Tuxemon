# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import logging

from tuxemon.monster import Monster
from tuxemon.tools import compare

logger = logging.getLogger(__name__)


class CommonPartyCondition:
    name = "Common Party"

    @staticmethod
    def check_party_parameter(
        party: list[Monster],
        attribute: str,
        value: str,
        operator: str,
        times: int,
    ) -> bool:
        """
        Check character's monsters attribute against a given value. How many times
        these given values are present in the party.

        Parameters:
            party: The party, the character's monsters.
            attribute: Name of the monster attribute to check (e.g. level).
            value: Value to check (related to the attribute) (e.g. 5 - level).
            operator: Numeric comparison operator. Accepted values are "less_than",
                "less_or_equal", "greater_than", "greater_or_equal", "equals"
                and "not_equals".
            times: Value to check with operator (how many times in the party?).

        eg. "check_party_parameter monsters,level,5,equals,1"
        translated: "is there 1 monster among the monsters at level 5? True/False"

        """

        # check for valid inputs
        # trigger an AttributeError if the attribute doesn't already exist
        attr = None
        check = []
        for monster in party:
            try:
                attr = getattr(monster, attribute)
            except AttributeError:
                logger.warning(
                    "Monster attribute '{0}' specified does not exist.",
                    attribute,
                )
                return False

            try:
                val = type(attr)(value)
            except TypeError:
                logger.warning(
                    "The value given cannot be parsed into the correct type for '{0}'",
                    attribute,
                )
                return False
            if attr == val:
                check.append(monster)
        return compare(operator, len(check), times)
