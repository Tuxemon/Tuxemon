# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import re

__version__ = "0.4.35"


class Version:
    """Represents the version of a plugin, following semantic versioning."""

    def __init__(
        self,
        major: int,
        minor: int,
        patch: int,
        pre_release: str = "",
        build_metadata: str = "",
    ):
        self.major = major
        self.minor = minor
        self.patch = patch
        self.pre_release = pre_release
        self.build_metadata = build_metadata

    def __str__(self) -> str:
        """Returns the string representation of the version."""
        version_str = f"{self.major}.{self.minor}.{self.patch}"
        if self.pre_release:
            version_str += f"-{self.pre_release}"
        if self.build_metadata:
            version_str += f"+{self.build_metadata}"
        return version_str

    @classmethod
    def from_string(cls, version_str: str) -> Version:
        """Creates a Version from a string, supporting pre-release and build metadata."""
        Version.validate_version(version_str)

        try:
            main_part, *rest = version_str.split("-")
            major, minor, patch = map(int, main_part.split("."))
            pre_release = ""
            build_metadata = ""

            if rest:
                pre_release = rest[0]
                if "+" in pre_release:
                    pre_release, build_metadata = pre_release.split("+", 1)

            return cls(major, minor, patch, pre_release, build_metadata)
        except ValueError:
            raise ValueError(
                f"Invalid version string: {version_str}. Expected format: MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]"
            )

    def __eq__(self, other: object) -> bool:
        """Checks if two Version instances are equal."""
        if not isinstance(other, Version):
            return NotImplemented
        return (
            self.major == other.major
            and self.minor == other.minor
            and self.patch == other.patch
            and self.pre_release == other.pre_release
            and self.build_metadata == other.build_metadata
        )

    def __lt__(self, other: Version) -> bool:
        """Compares two Version instances for less than."""
        if self.major != other.major:
            return self.major < other.major
        if self.minor != other.minor:
            return self.minor < other.minor
        if self.patch != other.patch:
            return self.patch < other.patch
        return self.pre_release < other.pre_release

    def __gt__(self, other: Version) -> bool:
        """Compares two Version instances for greater than."""
        return not (self < other or self == other)

    def __ge__(self, other: Version) -> bool:
        """Compares two Version instances for greater than or equal to."""
        return self > other or self == other

    @staticmethod
    def validate_version(version_str: str) -> None:
        """Validates the version string format."""
        if not re.match(
            r"^\d+\.\d+\.\d+(-[0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*)?(\+[0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*)?$",
            version_str,
        ):
            raise ValueError(
                f"Invalid version format: {version_str}. Expected format: MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]"
            )


class VersionComparator:
    @staticmethod
    def compare(version1: Version, version2: Version) -> int:
        """
        Compares two Version objects.

        Returns:
            -1 if version1 < version2
             0 if version1 == version2
             1 if version1 > version2
        """
        if version1.major != version2.major:
            return version1.major - version2.major
        if version1.minor != version2.minor:
            return version1.minor - version2.minor
        return version1.patch - version2.patch
