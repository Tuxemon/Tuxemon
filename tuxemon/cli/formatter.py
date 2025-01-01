# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import cmd
from collections.abc import Sequence
from typing import Optional


class Formatter:
    """
    Print formatted text things.

    Currently just supports printing things in a table.

    """

    def print_table(
        self,
        header: str,
        items: Sequence[str],
        footer: Optional[str],
        ruler: str = "=",
        maxcol: int = 120,
    ) -> None:
        """
        Print formatted table with header and footer.

        Parameters:
            header: Text to display as a heading.
            items: Items to display as a table.
            footer: Text to display after table.
            ruler: Character to use to underline the header.
            maxcol: Width of table in characters.

        """
        print(header)
        print(ruler * len(header))
        c = cmd.Cmd()
        c.columnize(list(items), maxcol)
        if footer is not None:
            print()
            print(footer)
