# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import textwrap
from collections.abc import Sequence
from itertools import dropwhile


class TextPaginator:
    """
    A class responsible for paginating text into a sequence of pages based on
    line length and page height constraints.
    If no constraints are provided, it defaults to newline-based pagination.
    """

    def __init__(
        self,
        max_line_length: int | None = None,
        max_lines_per_page: int | None = None,
        line_break_chars: str = "\n",
        strip_lines: bool = True,
    ):
        """
        Initializes the TextPaginator with display constraints.

        Parameters:
            max_line_length: Max number of characters per line (for wrapping).
            max_lines_per_page: Max lines per page (for pagination).
            line_break_chars: Characters used to split input into lines.
            strip_lines: Whether to strip whitespace from each line.
        """
        self.max_line_length = max_line_length
        self.max_lines_per_page = max_lines_per_page
        self.line_break_chars = line_break_chars
        self.strip_lines = strip_lines

    def paginate_text(self, text: str) -> Sequence[str]:
        """
        Splits the given text into a sequence of pages.

        - If no constraints are provided, splits by newline characters.
        - If constraints are set, applies word wrapping and page height limits.

        Returns:
            A list of page strings, each representing a chunk of text.
        """
        if self.max_line_length is None and self.max_lines_per_page is None:
            # Default behavior: just split by line breaks
            return text.rstrip("\n").split("\n")

        lines = self._normalize_and_wrap_text(text)
        lines = self._trim_blank_edges(lines)
        return self._chunk_lines_into_pages(lines)

    def _normalize_and_wrap_text(self, text: str) -> list[str]:
        """
        Breaks the input into lines and wraps them if line length is constrained.
        """
        raw_lines = text.split(self.line_break_chars)
        wrapped_lines: list[str] = []

        for line in raw_lines:
            if self.strip_lines:
                line = line.strip()

            if self.max_line_length:
                wrapped_lines.extend(
                    textwrap.wrap(
                        line,
                        width=self.max_line_length,
                        break_long_words=True,
                        break_on_hyphens=False,
                    )
                )
            else:
                wrapped_lines.append(line)

        return wrapped_lines

    def _trim_blank_edges(self, lines: list[str]) -> list[str]:
        """
        Removes blank lines from the beginning and end of the input.
        """
        trimmed_front = list(dropwhile(lambda l: not l.strip(), lines))
        trimmed_back = list(
            reversed(
                list(
                    dropwhile(lambda l: not l.strip(), reversed(trimmed_front))
                )
            )
        )
        return trimmed_back

    def _chunk_lines_into_pages(self, lines: list[str]) -> list[str]:
        """
        Chunks the lines into pages based on the max_lines_per_page constraint.
        """
        if self.max_lines_per_page is None:
            return [self.line_break_chars.join(lines)]

        pages: list[str] = []
        current_page: list[str] = []

        for line in lines:
            if len(current_page) >= self.max_lines_per_page:
                pages.append(self.line_break_chars.join(current_page))
                current_page = []

            current_page.append(line)

        if current_page:
            pages.append(self.line_break_chars.join(current_page))

        return pages
