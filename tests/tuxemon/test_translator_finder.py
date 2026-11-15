# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from tuxemon.locale.finder import LocaleFinder


@pytest.fixture
def temp_root():
    with TemporaryDirectory() as tmp:
        yield Path(tmp)


def test_init(temp_root):
    finder = LocaleFinder([temp_root])
    assert finder.root_dirs == (temp_root,)
    assert finder._scanned is False


def test_scan(temp_root):
    locale_dir = temp_root / "locale"
    locale_dir.mkdir()
    category_dir = locale_dir / "category"
    category_dir.mkdir()
    (category_dir / "example.po").touch()

    finder = LocaleFinder([temp_root], auto_scan=True)
    assert finder._scanned is True
    assert len(finder.get_locales()) == 1


def test_search_locales(temp_root):
    locale_dir = temp_root / "locale"
    locale_dir.mkdir()
    category_dir = locale_dir / "category"
    category_dir.mkdir()
    (category_dir / "example.po").touch()

    finder = LocaleFinder([temp_root])
    locales = list(finder.search_locales())
    assert len(locales) == 1


def test_has_locale(temp_root):
    locale_dir = temp_root / "locale"
    locale_dir.mkdir()
    category_dir = locale_dir / "category"
    category_dir.mkdir()
    (category_dir / "example.po").touch()

    finder = LocaleFinder([temp_root], auto_scan=True)
    assert finder.has_locale("locale")


def test_reset(temp_root):
    locale_dir = temp_root / "locale"
    locale_dir.mkdir()
    category_dir = locale_dir / "category"
    category_dir.mkdir()
    (category_dir / "example.po").touch()

    finder = LocaleFinder([temp_root], auto_scan=True)
    assert finder._scanned is True

    finder.reset()
    assert finder._scanned is False


def test_get_locales(temp_root):
    locale_dir = temp_root / "locale"
    locale_dir.mkdir()
    category_dir = locale_dir / "category"
    category_dir.mkdir()
    (category_dir / "example.po").touch()

    finder = LocaleFinder([temp_root], auto_scan=True)
    assert len(finder.get_locales()) == 1


def test_get_locale_names(temp_root):
    locale1 = temp_root / "locale1"
    locale2 = temp_root / "locale2"
    locale1.mkdir()
    locale2.mkdir()

    category = locale1 / "category"
    category.mkdir()
    (category / "example.po").touch()

    finder = LocaleFinder([temp_root], auto_scan=True)
    names = finder.get_locale_names()

    assert len(names) == 2
    assert "locale1" in names
    assert "locale2" in names


def test_invalid_root_dir():
    finder = LocaleFinder([Path("invalid_dir")])
    assert finder.root_dirs == (Path("invalid_dir"),)
    assert finder._scanned is False


def test_empty_root_dir(temp_root):
    finder = LocaleFinder([temp_root], auto_scan=True)
    assert finder._scanned is True
    assert len(finder.get_locales()) == 0


def test_multiple_root_dirs(temp_root):
    root1 = temp_root / "root1"
    root2 = temp_root / "root2"
    root1.mkdir()
    root2.mkdir()

    category1 = root1 / "locale1" / "category"
    category1.mkdir(parents=True)
    (category1 / "example1.po").touch()

    category2 = root2 / "locale2" / "category"
    category2.mkdir(parents=True)
    (category2 / "example2.po").touch()

    finder = LocaleFinder([root1, root2], auto_scan=True)
    locales = finder.get_locales()

    assert len(locales) == 2
    assert "locale1" in finder.get_locale_names()
    assert "locale2" in finder.get_locale_names()


def test_non_po_file_ignored(temp_root):
    category = temp_root / "locale" / "category"
    category.mkdir(parents=True)
    (category / "not_po.txt").touch()

    finder = LocaleFinder([temp_root], auto_scan=True)
    assert len(finder.get_locales()) == 0


def test_empty_category_dir(temp_root):
    category = temp_root / "locale" / "category"
    category.mkdir(parents=True)

    finder = LocaleFinder([temp_root], auto_scan=True)
    assert len(finder.get_locales()) == 0


def test_weird_extension_file(temp_root):
    category = temp_root / "locale" / "category"
    category.mkdir(parents=True)
    (category / "example.po.backup").touch()

    finder = LocaleFinder([temp_root], auto_scan=True)
    assert len(finder.get_locales()) == 0
