# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import MagicMock, patch

from tuxemon.locale import TranslatorPo


class TestTranslatorPo(unittest.TestCase):
    def setUp(self):
        self.locale_finder = MagicMock()
        self.gettext_compiler = MagicMock()
        self.translator = TranslatorPo(
            self.locale_finder, self.gettext_compiler
        )

    def test_collect_languages(self):
        self.translator.build_translations = MagicMock()
        self.translator.load_translator = MagicMock()
        self.translator.collect_languages()

        self.translator.build_translations.assert_called_once()
        self.translator.load_translator.assert_called_once_with(
            self.translator.locale_name
        )

    def test_build_translations(self):
        self.locale_finder.search_locales.return_value = [
            MagicMock(
                locale="en_US",
                category="general",
                domain="base",
                path="mock_path",
            )
        ]
        self.gettext_compiler.get_mo_path.return_value = "mock_mo_path"
        self.translator.build_translations(recompile_translations=True)

        self.gettext_compiler.compile_gettext.assert_called_once_with(
            "mock_path", "mock_mo_path"
        )

    @patch("gettext.translation")
    def test_load_translator(self, mock_translation):
        mock_translation.return_value = MagicMock()
        self.translator.load_translator(locale_name="en_US", domain="base")

        self.assertEqual(self.translator.locale_name, "en_US")

    def test_translate_with_cache(self):
        self.translator._real_translate = MagicMock(
            return_value="translated_message"
        )
        result = self.translator._translate_with_cache("test_message")

        self.assertEqual(result, "translated_message")
        self.assertIn("test_message", self.translator._translation_cache)

    def test_change_language(self):
        self.translator.is_language_supported = MagicMock(return_value=True)
        self.translator.load_translator = MagicMock()
        self.translator.language_changed = MagicMock()

        self.translator.change_language("fr_FR")
        self.translator.load_translator.assert_called_once_with("fr_FR")
        self.translator.language_changed.assert_called_once_with("fr_FR")

    def test_get_available_languages(self):
        self.locale_finder.locale_names = {"en_US", "fr_FR", "es_ES"}
        result = self.translator.get_available_languages()

        self.assertEqual(result, ["en_US", "es_ES", "fr_FR"])

    def test_has_translation(self):
        self.translator._get_translation = MagicMock(
            return_value=MagicMock(gettext=lambda x: "mock_translation")
        )
        result = self.translator.has_translation("en_US", "test_message")

        self.assertTrue(result)

    def test_maybe_translate(self):
        self.translator.translate = MagicMock(return_value="mock_translation")
        result = self.translator.maybe_translate("test_message")

        self.assertEqual(result, "mock_translation")

    def test_format(self):
        self.translator.translate = MagicMock(return_value="Hello, {name}!")
        result = self.translator.format("Hello, {name}!", {"name": "Alice"})

        self.assertEqual(result, "Hello, Alice!")
