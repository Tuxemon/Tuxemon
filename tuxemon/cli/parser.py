from __future__ import annotations

import shlex
from typing import List, Tuple


def parse(text: str) -> List[str]:
    """
    Default parser for text input on the prompt.

    Parameters:
        text: Text to split into tokens.

    """
    return shlex.split(text)


def split(line: str) -> Tuple[str, str]:
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
