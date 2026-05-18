# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tuxemon.locale.locale import TranslatorManager


@pytest.fixture
def locale_finder():
    return MagicMock()


@pytest.fixture
def gettext_compiler():
    return MagicMock()


@pytest.fixture
def manager(locale_finder, gettext_compiler):
    return TranslatorManager(locale_finder, gettext_compiler)


def test_collect_and_compile_translations(
    manager, locale_finder, gettext_compiler
):
    mock_info = MagicMock()
    mock_info.locale = "en"
    mock_info.category = "core"
    mock_info.domain = "base"
    mock_info.path = Path("dummy.po")

    locale_finder.search_locales.return_value = [mock_info]
    gettext_compiler.get_mo_path.return_value = Path("dummy.mo")
    gettext_compiler.compile_gettext = MagicMock()

    with patch.object(Path, "stat") as mock_stat:
        mock_stat.return_value.st_mtime = 1753513785.0

        manager.collect_and_compile_translations(recompile_translations=True)

    gettext_compiler.compile_gettext.assert_called_once()


def test_load_translator_for_domain(manager):
    manager.load_translator_for_domain("base", "en")
    assert "base" in manager._translators
    assert manager._translators["base"].locale_name == "en"


def test_translate_routing(manager):
    mock_po = MagicMock()
    mock_po.translate.return_value = "Hello"

    manager._translators["base"] = mock_po
    manager._current_translator_key = "base"

    result = manager.translate("Hi")
    assert result == "Hello"


def test_maybe_translate_none(manager):
    mock_po = MagicMock()
    mock_po.maybe_translate.return_value = ""

    manager._translators["base"] = mock_po
    manager._current_translator_key = "base"

    result = manager.maybe_translate(None)
    assert result == ""


def test_has_translation_true(manager):
    mock_po = MagicMock()
    mock_po.locale_name = "en"
    mock_po.has_translation.return_value = True

    manager._translators["base"] = mock_po

    result = manager.has_translation("en", "test_message", domain="base")
    assert result is True
