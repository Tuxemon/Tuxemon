# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from pathlib import Path

import pytest

from tuxemon.constants.paths import (
    ACTIONS_PATH,
    BASEDIR,
    CACHE_DIR,
    CONDITIONS_PATH,
    CORE_CONDITION_PATH,
    CORE_EFFECT_PATH,
    L18N_MO_FILES,
    LIBDIR,
    USER_CONFIG_PATH,
    USER_GAME_DATA_DIR,
    USER_GAME_SAVE_DIR,
    USER_RECORDING_DIR,
    get_active_mod_paths,
    get_mod_name_from_path,
    get_plugin_paths,
    mods_folder,
)


@pytest.fixture
def core_paths():
    return [
        LIBDIR,
        BASEDIR,
        CONDITIONS_PATH,
        ACTIONS_PATH,
        CORE_EFFECT_PATH,
        CORE_CONDITION_PATH,
        USER_GAME_DATA_DIR,
        USER_GAME_SAVE_DIR,
        CACHE_DIR,
        L18N_MO_FILES,
        USER_RECORDING_DIR,
    ]


def test_paths_exist(core_paths):
    for path in core_paths:
        assert path.exists(), f"Expected {path} to exist"


def test_mods_folder():
    folder = LIBDIR.parent / "mods"
    assert folder.exists()
    assert folder == mods_folder


def test_user_config_path():
    assert USER_CONFIG_PATH.parent.exists()


def test_get_active_mod_paths(tmp_path, monkeypatch):
    mods = tmp_path / "mods"
    mods.mkdir()
    (mods / "mod1").mkdir()
    (mods / ".hidden").mkdir()
    (mods / "__special").mkdir()
    (mods / "file.txt").write_text("not a dir")

    monkeypatch.setattr("tuxemon.constants.paths.mods_folder", mods)

    active = get_active_mod_paths()
    names = [p.name for p in active]
    assert "mod1" in names
    assert ".hidden" not in names
    assert "__special" not in names
    assert "file.txt" not in names


def test_get_plugin_paths(tmp_path, monkeypatch):
    base = tmp_path / "core" / "effects"
    base.mkdir(parents=True)
    mods = tmp_path / "mods"
    mods.mkdir()
    mod1 = mods / "mod1" / "effects"
    mod1.mkdir(parents=True)

    monkeypatch.setattr("tuxemon.constants.paths.mods_folder", mods)

    paths = get_plugin_paths(base, "effects")
    assert base in paths
    assert mod1 in paths


def test_get_mod_name_from_path_valid():
    p = Path("/game/mods/mymod/file.txt")
    assert get_mod_name_from_path(p) == "mymod"


def test_get_mod_name_from_path_no_mods():
    p = Path("/game/core/effects/file.txt")
    assert get_mod_name_from_path(p) is None


def test_get_mod_name_from_path_only_mods():
    p = Path("/game/mods")
    assert get_mod_name_from_path(p) is None
