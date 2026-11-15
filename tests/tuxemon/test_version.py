# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import pytest

from tuxemon.version import (
    Version,
    VersionComparator,
    __version__,
    version_info,
)


def test_string_roundtrip():
    v = Version("1.2.3")
    assert str(v) == "1.2.3"


@pytest.mark.parametrize(
    "input_str",
    [
        pytest.param("1.2.3", id="simple_release"),
        pytest.param("1.2.3a1", id="alpha_release"),
        pytest.param("1.2.3b2", id="beta_release"),
        pytest.param("1.2.3rc3", id="release_candidate"),
        pytest.param("1.2.3.post1", id="post_release"),
        pytest.param("1.2.3.dev4", id="dev_release"),
        pytest.param("1!1.2.3", id="epoch_version"),
        pytest.param("1.2.3+local", id="local_version"),
    ],
)
def test_valid_pep440_versions(input_str):
    Version(input_str)  # should not raise


@pytest.mark.parametrize(
    "invalid",
    [
        pytest.param("1.2.x", id="invalid_character"),
        pytest.param("1..3", id="empty_segment"),
        pytest.param("1.2.3-foo", id="invalid_prerelease_semver_style"),
        pytest.param("1.2.3+foo+bar", id="invalid_multiple_local_segments"),
    ],
)
def test_invalid_pep440_versions(invalid):
    with pytest.raises(ValueError):
        Version(invalid)


def test_equality():
    assert Version("1.2.3") == Version("1.2.3")
    assert Version("1.2.3") != Version("1.2.4")


def test_comparison():
    assert Version("1.2.3") < Version("1.2.4")
    assert Version("1.2.3a1") < Version("1.2.3b1")
    assert Version("1.2.3b1") < Version("1.2.3rc1")
    assert Version("1.2.3rc1") < Version("1.2.3")
    assert Version("1.2.3") < Version("1.2.3.post1")
    assert Version("1.2.3.dev1") < Version("1.2.3")


@pytest.mark.parametrize(
    "v1, v2, expected",
    [
        pytest.param(
            Version("1.2.3"), Version("1.2.3"), 0, id="equal_versions"
        ),
        pytest.param(
            Version("1.2.4"), Version("1.2.3"), 1, id="v1_greater_patch"
        ),
        pytest.param(
            Version("1.2.3"), Version("1.2.4"), -1, id="v1_smaller_patch"
        ),
        pytest.param(
            Version("2.0.0"), Version("1.9.9"), 1, id="v1_major_greater"
        ),
        pytest.param(
            Version("1.0.0"), Version("2.0.0"), -1, id="v1_major_smaller"
        ),
    ],
)
def test_version_comparator(v1, v2, expected):
    assert VersionComparator.compare(v1, v2) == expected


def test_dunder_version_is_string():
    assert isinstance(__version__, str)


def test_version_info_contains_dunder_version():
    assert __version__ in version_info()
