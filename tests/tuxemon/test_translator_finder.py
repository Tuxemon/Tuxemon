# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tuxemon.locale_dir.finder import LocaleFinder


class TestLocaleFinder(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = TemporaryDirectory()
        self.root_dir = Path(self.tmp_dir.name)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_init(self):
        locale_finder = LocaleFinder([self.root_dir])
        self.assertEqual(locale_finder.root_dirs, (self.root_dir,))
        self.assertFalse(locale_finder._scanned)

    def test_scan(self):
        locale_dir = self.root_dir / "locale"
        locale_dir.mkdir()
        category_dir = locale_dir / "category"
        category_dir.mkdir()
        file_path = category_dir / "example.po"
        file_path.touch()

        locale_finder = LocaleFinder([self.root_dir], auto_scan=True)
        self.assertTrue(locale_finder._scanned)
        self.assertEqual(len(locale_finder.get_locales()), 1)

    def test_search_locales(self):
        locale_dir = self.root_dir / "locale"
        locale_dir.mkdir()
        category_dir = locale_dir / "category"
        category_dir.mkdir()
        file_path = category_dir / "example.po"
        file_path.touch()

        locale_finder = LocaleFinder([self.root_dir])
        locales = list(locale_finder.search_locales())
        self.assertEqual(len(locales), 1)

    def test_has_locale(self):
        locale_dir = self.root_dir / "locale"
        locale_dir.mkdir()
        category_dir = locale_dir / "category"
        category_dir.mkdir()
        file_path = category_dir / "example.po"
        file_path.touch()

        locale_finder = LocaleFinder([self.root_dir], auto_scan=True)
        self.assertTrue(locale_finder.has_locale("locale"))

    def test_reset(self):
        locale_dir = self.root_dir / "locale"
        locale_dir.mkdir()
        category_dir = locale_dir / "category"
        category_dir.mkdir()
        file_path = category_dir / "example.po"
        file_path.touch()

        locale_finder = LocaleFinder([self.root_dir], auto_scan=True)
        self.assertTrue(locale_finder._scanned)
        locale_finder.reset()
        self.assertFalse(locale_finder._scanned)

    def test_get_locales(self):
        locale_dir = self.root_dir / "locale"
        locale_dir.mkdir()
        category_dir = locale_dir / "category"
        category_dir.mkdir()
        file_path = category_dir / "example.po"
        file_path.touch()

        locale_finder = LocaleFinder([self.root_dir], auto_scan=True)
        locales = locale_finder.get_locales()
        self.assertEqual(len(locales), 1)

    def test_get_locale_names(self):
        locale_dir1 = self.root_dir / "locale1"
        locale_dir1.mkdir()
        locale_dir2 = self.root_dir / "locale2"
        locale_dir2.mkdir()
        category_dir = locale_dir1 / "category"
        category_dir.mkdir()
        file_path = category_dir / "example.po"
        file_path.touch()

        locale_finder = LocaleFinder([self.root_dir], auto_scan=True)
        locale_names = locale_finder.get_locale_names()
        self.assertEqual(len(locale_names), 2)

    def test_invalid_root_dir(self):
        locale_finder = LocaleFinder([Path("invalid_dir")])
        self.assertEqual(locale_finder.root_dirs, (Path("invalid_dir"),))
        self.assertFalse(locale_finder._scanned)

    def test_empty_root_dir(self):
        locale_finder = LocaleFinder([self.root_dir], auto_scan=True)
        self.assertTrue(locale_finder._scanned)
        self.assertEqual(len(locale_finder.get_locales()), 0)

    def test_multiple_root_dirs(self):
        root1 = self.root_dir / "root1"
        root2 = self.root_dir / "root2"
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
        self.assertEqual(len(locales), 2)
        self.assertIn("locale1", finder.get_locale_names())
        self.assertIn("locale2", finder.get_locale_names())

    def test_non_po_file_ignored(self):
        locale_dir = self.root_dir / "locale"
        category_dir = locale_dir / "category"
        category_dir.mkdir(parents=True)
        (category_dir / "not_po.txt").touch()

        finder = LocaleFinder([self.root_dir], auto_scan=True)
        self.assertEqual(len(finder.get_locales()), 0)

    def test_empty_category_dir(self):
        locale_dir = self.root_dir / "locale"
        category_dir = locale_dir / "category"
        category_dir.mkdir(parents=True)

        finder = LocaleFinder([self.root_dir], auto_scan=True)
        self.assertEqual(len(finder.get_locales()), 0)

    def test_weird_extension_file(self):
        locale_dir = self.root_dir / "locale"
        category_dir = locale_dir / "category"
        category_dir.mkdir(parents=True)
        (category_dir / "example.po.backup").touch()

        finder = LocaleFinder([self.root_dir], auto_scan=True)
        self.assertEqual(len(finder.get_locales()), 0)
