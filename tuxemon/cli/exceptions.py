# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
class CommandNotFoundError(Exception):
    """
    Raised when a command is not found.

    """


class ParseError(Exception):
    """
    Raised when the input cannot be parsed due to bad syntax.

    """
