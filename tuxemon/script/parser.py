# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import re
from collections.abc import Sequence


def split_escaped(string_to_split: str, delimeter: str = ",") -> Sequence[str]:
    """
    Splits a string by the specified deliminator excluding escaped ones.

    Parameters:
        string_to_split: The string to split.
        delimeter: The deliminator to split the string by.

    Returns:
        A list of the split string.
    """
    if not string_to_split.strip():
        return []

    # Split by delimiter unless it is escaped by a "\"
    split_list = re.split(r"(?<!\\)" + delimeter, string_to_split)

    # Clean up segments:
    # 1. Replace escaped delimiters
    # 2. Strip whitespace
    # 3. Filter out empty strings
    return [
        item.replace(f"\\{delimeter}", delimeter).strip()
        for item in split_list
    ]


def parse_action_string(text: str) -> tuple[str, Sequence[str]]:
    words = text.split(" ", 1)
    act_type = words[0]
    if len(words) > 1:
        args = split_escaped(words[1])
    else:
        args = list()
    return act_type, args


def parse_condition_string(text: str) -> tuple[str, str, Sequence[str]]:
    words = text.split(" ", 2)
    operator, cond_type = words[0:2]
    if len(words) > 2:
        args = split_escaped(words[2])
    else:
        args = list()
    return operator, cond_type, args


def parse_behav_string(behav_string: str) -> tuple[str, Sequence[str]]:
    words = behav_string.split(" ", 1)
    behav_type = words[0]
    if len(words) > 1:
        args = split_escaped(words[1])
    else:
        args = list()
    return behav_type, args
