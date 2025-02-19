# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import shlex


def parse(text: str) -> list[str]:
    """
    Default parser for text input on the prompt.

    Parameters:
        text: Text to split into tokens.

    """
    return shlex.split(text)


def split(line: str) -> tuple[str, str]:
    """
    Split text into head, tail tokens.  Text is split after 1st space.

    Parameters:
        line: Text to split.

    """
    try:
        index = line.index(" ")
        return line[:index], line[index:].lstrip()
    except ValueError:
        return line, ""
