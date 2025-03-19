# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest

from tuxemon.version import Version, VersionComparator


class TestVersion(unittest.TestCase):

    def test_initialization(self):
        version = Version(1, 2, 3)
        self.assertEqual(version.major, 1)
        self.assertEqual(version.minor, 2)
        self.assertEqual(version.patch, 3)
        self.assertEqual(version.pre_release, "")
        self.assertEqual(version.build_metadata, "")

    def test_string_representation(self):
        version = Version(1, 2, 3, "alpha", "001")
        self.assertEqual(str(version), "1.2.3-alpha+001")

    def test_from_string(self):
        version = Version.from_string("1.2.3-alpha+001")
        self.assertEqual(version.major, 1)
        self.assertEqual(version.minor, 2)
        self.assertEqual(version.patch, 3)
        self.assertEqual(version.pre_release, "alpha")
        self.assertEqual(version.build_metadata, "001")

    def test_from_string_invalid(self):
        with self.assertRaises(ValueError):
            Version.from_string("invalid.version.string")

    def test_equality(self):
        version1 = Version(1, 2, 3)
        version2 = Version(1, 2, 3)
        version3 = Version(1, 2, 4)
        self.assertTrue(version1 == version2)
        self.assertFalse(version1 == version3)

    def test_inequality(self):
        version1 = Version(1, 2, 3)
        version2 = Version(1, 2, 4)
        self.assertTrue(version1 != version2)

    def test_less_than(self):
        version1 = Version(1, 2, 3)
        version2 = Version(1, 2, 4)
        self.assertTrue(version1 < version2)

    def test_less_than_equal(self):
        version1 = Version(1, 2, 3)
        version2 = Version(1, 2, 3)
        version3 = Version(1, 2, 4)
        self.assertTrue(version1 <= version2)
        self.assertTrue(version1 <= version3)

    def test_greater_than(self):
        version1 = Version(1, 2, 4)
        version2 = Version(1, 2, 3)
        self.assertTrue(version1 > version2)

    def test_greater_than_equal(self):
        version1 = Version(1, 2, 3)
        version2 = Version(1, 2, 3)
        version3 = Version(1, 2, 2)
        self.assertTrue(version1 >= version2)
        self.assertTrue(version1 >= version3)

    def test_validate_version(self):
        Version.validate_version("1.2.3")
        Version.validate_version("1.2.3-alpha")
        Version.validate_version("1.2.3-alpha+001")
        Version.validate_version("1.2.3+001")

        with self.assertRaises(ValueError):
            Version.validate_version("1.2")
        with self.assertRaises(ValueError):
            Version.validate_version("1.2.3.4")
        with self.assertRaises(ValueError):
            Version.validate_version("invalid.version")


class TestVersionComparator(unittest.TestCase):

    def test_compare_equal(self):
        version1 = Version(1, 2, 3)
        version2 = Version(1, 2, 3)
        self.assertEqual(VersionComparator.compare(version1, version2), 0)

    def test_compare_greater(self):
        version1 = Version(1, 2, 4)
        version2 = Version(1, 2, 3)
        self.assertEqual(VersionComparator.compare(version1, version2), 1)

    def test_compare_less(self):
        version1 = Version(1, 2, 3)
        version2 = Version(1, 2, 4)
        self.assertEqual(VersionComparator.compare(version1, version2), -1)

    def test_compare_major_difference(self):
        version1 = Version(2, 0, 0)
        version2 = Version(1, 9, 9)
        self.assertEqual(VersionComparator.compare(version1, version2), 1)

        version1 = Version(1, 0, 0)
        version2 = Version(2, 0, 0)
        self.assertEqual(VersionComparator.compare(version1, version2), -1)

    def test_compare_minor_difference(self):
        version1 = Version(1, 1, 0)
        version2 = Version(1, 2, 0)
        self.assertEqual(VersionComparator.compare(version1, version2), -1)

        version1 = Version(1, 2, 0)
        version2 = Version(1, 1, 0)
        self.assertEqual(VersionComparator.compare(version1, version2), 1)

    def test_compare_patch_difference(self):
        version1 = Version(1, 2, 3)
        version2 = Version(1, 2, 4)
        self.assertEqual(VersionComparator.compare(version1, version2), -1)

        version1 = Version(1, 2, 4)
        version2 = Version(1, 2, 3)
        self.assertEqual(VersionComparator.compare(version1, version2), 1)
