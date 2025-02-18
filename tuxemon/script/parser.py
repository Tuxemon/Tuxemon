# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import re
from collections.abc import Sequence


def split_escaped(
    string_to_split: str,
    delimeter: str = ",",
) -> Sequence[str]:
    """
    Splits a string by the specified deliminator excluding escaped ones.

    Parameters:
        string_to_split: The string to split.
        delimeter: The deliminator to split the string by.

    Returns:
        A list of the split string.

    """
    # Split by "," unless it is escaped by a "\"
    split_list = re.split(r"(?<!\\)" + delimeter, string_to_split)

    # Remove the escape character from the split list
    split_list = [w.replace(r"\,", ",") for w in split_list]

    # strip whitespace around each
    split_list = [i.strip() for i in split_list]

    return split_list


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
