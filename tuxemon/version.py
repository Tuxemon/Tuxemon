# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from packaging.version import InvalidVersion
from packaging.version import Version as PEP440Version

try:
    __version__ = version("tuxemon")
except PackageNotFoundError:
    __version__ = "0.0.0-dev"


def version_info() -> str:
    """Returns a human-readable version string for display or debugging."""
    return f"Tuxemon version {__version__}"


class Version:
    """
    A strict PEP 440 version wrapper.

    This class delegates all parsing, normalization, and comparison
    to packaging.version.Version to ensure full PEP 440 compliance.
    """

    def __init__(self, version_str: str):
        try:
            self._v = PEP440Version(version_str)
        except InvalidVersion as e:
            raise ValueError(f"Invalid PEP 440 version: {version_str}") from e

    def __str__(self) -> str:
        return str(self._v)

    def __repr__(self) -> str:
        return f"Version('{self._v}')"

    @classmethod
    def from_string(cls, version_str: str) -> Version:
        return cls(version_str)

    # Comparison operators simply delegate to packaging.version.Version
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self._v == other._v

    def __lt__(self, other: Version) -> bool:
        return self._v < other._v

    def __le__(self, other: Version) -> bool:
        return self._v <= other._v

    def __gt__(self, other: Version) -> bool:
        return self._v > other._v

    def __ge__(self, other: Version) -> bool:
        return self._v >= other._v


class VersionComparator:
    @staticmethod
    def compare(version1: Version, version2: Version) -> int:
        if version1 < version2:
            return -1
        if version1 > version2:
            return 1
        return 0
