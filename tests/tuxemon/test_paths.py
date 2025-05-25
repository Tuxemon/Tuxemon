# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from pathlib import Path

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
    mods_folder,
)


class TestCorePaths(unittest.TestCase):

    def test_libdir(self):
        self.assertTrue(LIBDIR.exists())

    def test_basedir(self):
        self.assertTrue(BASEDIR.exists())

    def test_mods_folder(self):
        folder = LIBDIR.parent / "mods"
        self.assertTrue(folder.exists())
        self.assertEqual(folder, mods_folder)

    def test_event_paths(self):
        self.assertTrue(CONDITIONS_PATH.exists())
        self.assertTrue(ACTIONS_PATH.exists())

    def test_core_paths(self):
        self.assertTrue(CORE_EFFECT_PATH.exists())
        self.assertTrue(CORE_CONDITION_PATH.exists())

    def test_user_config_path(self):
        self.assertTrue(USER_CONFIG_PATH.parent.exists())

    def test_user_game_data_dir(self):
        self.assertTrue(USER_GAME_DATA_DIR.exists())

    def test_user_game_save_dir(self):
        self.assertTrue(USER_GAME_SAVE_DIR.exists())

    def test_cache_dir(self):
        self.assertTrue(CACHE_DIR.exists())

    def test_l18n_mo_files(self):
        self.assertTrue(L18N_MO_FILES.exists())
