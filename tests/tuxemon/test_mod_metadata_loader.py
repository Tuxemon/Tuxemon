# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from tuxemon.constants.paths import mods_folder
from tuxemon.database.management import ModMetadataLoader


def test_relative_base_path_is_resolved_against_the_game():
    loader = ModMetadataLoader(["tuxemon"], "mods")
    assert loader.base_path == mods_folder


def test_absolute_base_path_is_left_alone(tmp_path):
    loader = ModMetadataLoader(["tuxemon"], tmp_path)
    assert loader.base_path == tmp_path


def test_metadata_is_found_from_any_working_directory(monkeypatch, tmp_path):
    # packaged builds (flatpak, cx_freeze) are launched from wherever the
    # user happens to be, not from the folder holding the mods
    monkeypatch.chdir(tmp_path)

    metadata = ModMetadataLoader(["tuxemon"]).load_metadata()

    assert "tuxemon" in metadata
    assert metadata["tuxemon"].slug == "tuxemon"


def test_missing_metadata_is_skipped(tmp_path):
    metadata = ModMetadataLoader(["nonexistent"], tmp_path).load_metadata()
    assert metadata == {}
