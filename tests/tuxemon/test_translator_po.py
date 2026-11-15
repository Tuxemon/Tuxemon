# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from pathlib import Path
from unittest.mock import MagicMock, patch

from tuxemon.locale.translator import TranslatorPo


@patch("tuxemon.locale.translator.translation")
def test_translation_success(mock_translation):
    mock_trans = MagicMock()
    mock_trans.gettext.return_value = "Bonjour"
    mock_translation.return_value = mock_trans

    po = TranslatorPo(
        locale_name="fr",
        domain="base",
        localedir=Path("."),
        fallback_locale="en",
    )

    result = po.translate("Hello")
    assert result == "Bonjour"


@patch("tuxemon.locale.translator.translation", side_effect=FileNotFoundError)
def test_fallback_to_null_translations(mock_translation):
    po = TranslatorPo(
        locale_name="xx",
        domain="base",
        localedir=Path("."),
        fallback_locale="en",
    )
    result = po.translate("Hello")
    assert result == "Hello"  # untranslated fallback


def test_format_translation():
    po = TranslatorPo("en", "base", Path("."), "en")
    po.translate = MagicMock(return_value="Hello, {name}")

    result = po.format("Hello, {name}", {"name": "Alice"})
    assert result == "Hello, Alice"


def test_maybe_translate_none():
    po = TranslatorPo("en", "base", Path("."), "en")
    assert po.maybe_translate(None) == ""


def test_maybe_translate_string():
    po = TranslatorPo("en", "base", Path("."), "en")
    po.translate = MagicMock(return_value="Hi")
    assert po.maybe_translate("Hello") == "Hi"


@patch("tuxemon.locale.translator.translation")
def test_plural_translation_success(mock_translation):
    mock_trans = MagicMock()
    mock_trans.ngettext.side_effect = lambda s, p, n: (
        f"{n} apple" if n == 1 else f"{n} apples"
    )

    mock_fallback = MagicMock()
    mock_fallback.ngettext.side_effect = lambda s, p, n: f"{n} fallback"

    mock_translation.side_effect = [mock_trans, mock_fallback]

    po = TranslatorPo("en", "base", Path("."), "en")

    singular = "apple"
    plural = "apples"

    result_one = po.translate_plural(singular, plural, 1)
    result_many = po.translate_plural(singular, plural, 3)

    assert result_one == "1 apple"
    assert result_many == "3 apples"


@patch("tuxemon.locale.translator.translation")
def test_has_translation(mock_translation):
    mock_trans = MagicMock()
    mock_trans.gettext.side_effect = lambda msg: (
        "Bonjour" if msg == "Hello" else msg
    )

    mock_fallback = MagicMock()
    mock_fallback.gettext.side_effect = lambda msg: msg

    mock_translation.side_effect = [mock_trans, mock_fallback]

    po = TranslatorPo("fr", "base", Path("."), "en")

    assert po.has_translation("Hello")
    assert not po.has_translation("Goodbye")


@patch("tuxemon.locale.translator.translation")
def test_has_plural_translation(mock_translation):
    mock_trans = MagicMock()
    mock_trans.ngettext.side_effect = lambda s, p, n: s if n == 1 else p

    mock_fallback = MagicMock()
    mock_fallback.ngettext.side_effect = lambda s, p, n: s if n == 1 else p

    mock_translation.side_effect = [mock_trans, mock_fallback]

    po = TranslatorPo("en", "base", Path("."), "en")

    assert not po.has_plural_translation("apple", "apples", 0)


@patch("tuxemon.locale.translator.translation", side_effect=FileNotFoundError)
def test_missing_all_translations(mock_translation):
    po = TranslatorPo("xx", "base", Path("."), "yy")
    result = po.translate("Hello")
    assert result == "Hello"


def test_get_current_language():
    po = TranslatorPo("it", "base", Path("."), "en")
    assert po.get_current_language() == "it"
