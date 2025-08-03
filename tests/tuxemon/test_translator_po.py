# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from tuxemon.locale import TranslatorPo


class TestTranslatorPo(unittest.TestCase):

    @patch("gettext.translation")
    def test_translation_success(self, mock_translation):
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
        self.assertEqual(result, "Bonjour")

    @patch("gettext.translation", side_effect=FileNotFoundError)
    def test_fallback_to_null_translations(self, mock_translation):
        po = TranslatorPo(
            locale_name="xx",
            domain="base",
            localedir=Path("."),
            fallback_locale="en",
        )
        result = po.translate("Hello")
        self.assertEqual(result, "Hello")  # Should be untranslated

    def test_translate_with_cache(self):
        po = TranslatorPo(
            locale_name="xx",
            domain="base",
            localedir=Path("."),
            fallback_locale="en",
        )
        po._real_translate = MagicMock(return_value="Hi")
        result = po.translate("Hello")
        self.assertEqual(result, "Hi")
        self.assertIn("Hello", po._translation_cache)

    def test_format_translation(self):
        po = TranslatorPo(
            locale_name="en",
            domain="base",
            localedir=Path("."),
            fallback_locale="en",
        )
        po.translate = MagicMock(return_value="Hello, {name}")
        result = po.format("Hello, {name}", {"name": "Alice"})
        self.assertEqual(result, "Hello, Alice")

    def test_maybe_translate_none(self):
        po = TranslatorPo("en", "base", Path("."), "en")
        result = po.maybe_translate(None)
        self.assertEqual(result, "")
