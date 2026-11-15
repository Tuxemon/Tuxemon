# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import shlex


def parse(text: str) -> list[str]:
    """
    Default parser for text input on the prompt.

    Parameters:
        text: Text to split into tokens.
    """
    return shlex.split(text)


def tokenize(line: str) -> list[str]:
    """
    Tokenize a command line into whitespace-separated tokens.

    This is intentionally simple and preserves current behavior:
    - No normalization beyond splitting on spaces.
    - Empty or all-space strings return [].
    """
    line = line.strip()
    if not line:
        return []
    return line.split(" ")
