# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tuxemon.event.actions.translated_dialog_choice import (
    TranslatedDialogChoiceAction,
)

MODULE = "tuxemon.event.actions.translated_dialog_choice"


def _open(*params: str) -> dict:
    session = MagicMock()
    action = TranslatedDialogChoiceAction("a:b", "pick", *params)
    with (
        patch(f"{MODULE}.open_choice_dialog") as opened,
        patch(f"{MODULE}.TextFormatter.replace_text", return_value="a:b"),
        patch(f"{MODULE}.create_choice_options", return_value=[]),
        patch(f"{MODULE}.T.translate", side_effect=lambda k: f"<{k}>"),
    ):
        action.start(session)
    return opened.call_args.kwargs


@pytest.mark.parametrize(
    "params, exits, title",
    [
        pytest.param((), True, None, id="plain-back-closes"),
        pytest.param(
            ("must",), False, None, id="must-alone-back-does-nothing"
        ),
        pytest.param(("other",), True, "<other>", id="word-is-a-title"),
        pytest.param(("head",), True, "<head>", id="title-alone"),
        pytest.param(("head", "must"), False, "<head>", id="title-and-must"),
        pytest.param(("head", "x"), True, "<head>", id="title-and-other-word"),
        pytest.param(("", "must"), False, None, id="empty-title-and-must"),
    ],
)
def test_title_and_must(params, exits, title):
    kwargs = _open(*params)
    assert kwargs["escape_key_exits"] is exits
    assert kwargs["title"] == title


def test_first_option_scrolls_a_titled_list_back_to_its_title() -> None:
    from pygame_menu.locals import ORIENTATION_VERTICAL

    from tuxemon.states.choice_state import ChoiceState

    menu = MagicMock()
    ChoiceState._show_title(True, MagicMock(), menu)
    menu.get_scrollarea().scroll_to.assert_called_once_with(
        ORIENTATION_VERTICAL, 0
    )


def test_leaving_the_first_option_does_not_scroll() -> None:
    from tuxemon.states.choice_state import ChoiceState

    menu = MagicMock()
    ChoiceState._show_title(False, MagicMock(), menu)
    menu.get_scrollarea().scroll_to.assert_not_called()
