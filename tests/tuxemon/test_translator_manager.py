# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from tuxemon.locale import TranslatorManager


class TestTranslatorManager(unittest.TestCase):

    def setUp(self):
        self.locale_finder = MagicMock()
        self.gettext_compiler = MagicMock()
        self.manager = TranslatorManager(
            self.locale_finder, self.gettext_compiler
        )

    def test_collect_and_compile_translations(self):
        mock_info = MagicMock()
        mock_info.locale = "en"
        mock_info.category = "core"
        mock_info.domain = "base"
        mock_info.path = Path("dummy.po")

        self.locale_finder.search_locales.return_value = [mock_info]
        self.gettext_compiler.get_mo_path.return_value = Path("dummy.mo")
        self.gettext_compiler.compile_gettext = MagicMock()

        self.manager.collect_and_compile_translations(
            recompile_translations=True
        )
        self.gettext_compiler.compile_gettext.assert_called_once()

    def test_load_translator_for_domain(self):
        self.manager.load_translator_for_domain("base", "en")
        self.assertIn("base", self.manager._translators)
        self.assertEqual(self.manager._translators["base"].locale_name, "en")

    def test_translate_routing(self):
        mock_po = MagicMock()
        mock_po.translate.return_value = "Hello"
        self.manager._translators["base"] = mock_po
        self.manager._current_translator_key = "base"

        result = self.manager.translate("Hi")
        self.assertEqual(result, "Hello")

    def test_maybe_translate_none(self):
        mock_po = MagicMock()
        mock_po.maybe_translate.return_value = ""
        self.manager._translators["base"] = mock_po
        self.manager._current_translator_key = "base"

        result = self.manager.maybe_translate(None)
        self.assertEqual(result, "")

    def test_has_translation_true(self):
        mock_po = MagicMock()
        mock_po.locale_name = "en"
        mock_po.has_translation.return_value = True
        self.manager._translators["base"] = mock_po

        result = self.manager.has_translation(
            "en", "test_message", domain="base"
        )
        self.assertTrue(result)
