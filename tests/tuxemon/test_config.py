# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import io
import threading
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

import pygame
import yaml

from tuxemon.config import (
    ControlsConfig,
    InputConfig,
    LoggingConfig,
    TuxemonConfig,
    TuxemonFullConfig,
)


def write_yaml(dir_path: Path, data) -> Path:
    p = dir_path / "tuxemon.yaml"
    p.write_text(yaml.safe_dump(data))
    return p


class TestTuxemonConfig(unittest.TestCase):
    def test_defaults_load_when_no_file(self):
        cfg = TuxemonConfig(config_path=None)
        self.assertIsNotNone(cfg.config_model)
        self.assertEqual(cfg.resolution, (1280, 720))
        self.assertEqual(cfg.dialog_speed, "slow")

    def test_load_partial_yaml_merges_with_defaults(self):
        with TemporaryDirectory() as td:
            td = Path(td)
            partial = {
                "display": {"resolution_x": 800},
                "gameplay": {"music_volume": 0.75},
            }
            path = write_yaml(td, partial)
            cfg = TuxemonConfig(config_path=path)
            self.assertEqual(cfg.resolution[0], 800)
            self.assertAlmostEqual(cfg.music_volume, 0.75)
            self.assertEqual(cfg.resolution[1], 720)
            self.assertEqual(cfg.dialog_speed, "slow")

    def test_invalid_enum_falls_back_to_defaults_and_reports(self):
        with (
            TemporaryDirectory() as td,
            mock.patch("sys.stdout", new_callable=io.StringIO) as fake_out,
        ):
            td = Path(td)
            bad = {
                "gameplay": {"dialog_speed": "ultra_fast"},
                "display": {"fps": 120},
            }
            path = write_yaml(td, bad)
            cfg = TuxemonConfig(config_path=path)
            output = fake_out.getvalue()
            self.assertIn("Configuration validation failed", output)
            self.assertEqual(cfg.dialog_speed, "slow")
            self.assertEqual(cfg.fps, 60.0)

    def test_volume_clamping_and_validation(self):
        data = TuxemonFullConfig().model_dump()
        data["gameplay"]["sound_volume"] = -1.0
        data["gameplay"]["music_volume"] = 2.0
        model = TuxemonFullConfig.model_validate(data)
        self.assertEqual(model.gameplay.sound_volume, 0.0)
        self.assertEqual(model.gameplay.music_volume, 1.0)

    def test_update_locale_writes_font_fields(self):
        with TemporaryDirectory() as td:
            td = Path(td)
            base = TuxemonFullConfig().model_dump()
            cfg_path = write_yaml(td, base)
            cfg = TuxemonConfig(config_path=cfg_path)

            cfg.update_locale("zh_CN")
            self.assertEqual(cfg.config_model.game.locale, "zh_CN")
            self.assertIn("SourceHanSerifCN", cfg.config_model.game.font_file)
            self.assertIn(
                "SourceHanSerifCN", cfg.config_model.game.thin_font_file
            )

            cfg.update_locale("ja")
            self.assertIn("SourceHanSerifJP", cfg.config_model.game.font_file)

            cfg.update_locale("en_US")
            self.assertEqual(
                cfg.config_model.game.font_file, "PressStart2P.ttf"
            )

    def test_reset_controls_to_default(self):
        with TemporaryDirectory() as td:
            td = Path(td)
            base = TuxemonFullConfig().model_dump()
            cfg_path = write_yaml(td, base)
            cfg = TuxemonConfig(config_path=cfg_path)

            cfg.input.update_key("up", "w")
            self.assertEqual(cfg.config_model.controls.up, "w")
            cfg.reset_controls_to_default()
            self.assertEqual(cfg.config_model.controls, ControlsConfig())
            self.assertIn(None, cfg.input.keyboard_button_map)

    def test_reload_config_applies_changes(self):
        with TemporaryDirectory() as td:
            td = Path(td)
            base = TuxemonFullConfig().model_dump()
            path = write_yaml(td, base)
            cfg = TuxemonConfig(config_path=path)
            new = base.copy()
            new["display"]["resolution_x"] = 640
            path.write_text(yaml.safe_dump(new))
            cfg.reload_config()
            self.assertEqual(cfg.resolution[0], 640)

    def test_save_load_roundtrip_full(self):
        with TemporaryDirectory() as td:
            td = Path(td)
            base = TuxemonFullConfig().model_dump()
            cfg_path = write_yaml(td, base)
            cfg = TuxemonConfig(config_path=cfg_path)

            cfg.config_model.display.resolution_x = 999
            cfg.config_model.game.locale = "ja"
            cfg.config_model.gameplay.sound_volume = 0.33
            cfg.config_model.graphics.menu_sound = "new_sound"
            cfg.config_model.player.player_runrate = 9.99
            cfg.save_config()

            cfg2 = TuxemonConfig(config_path=cfg_path)
            self.assertEqual(cfg2.config_model.display.resolution_x, 999)
            self.assertEqual(cfg2.config_model.game.locale, "ja")
            self.assertAlmostEqual(
                cfg2.config_model.gameplay.sound_volume, 0.33
            )
            self.assertEqual(
                cfg2.config_model.graphics.menu_sound, "new_sound"
            )
            self.assertAlmostEqual(
                cfg2.config_model.player.player_runrate, 9.99
            )

    def test_concurrent_read_write_race(self):
        with TemporaryDirectory() as td:
            td = Path(td)
            base = TuxemonFullConfig().model_dump()
            cfg_path = write_yaml(td, base)
            cfg = TuxemonConfig(config_path=cfg_path)

            stop = threading.Event()

            def writer():
                i = 0
                while not stop.is_set():
                    cfg.config_model.display.resolution_x = 1000 + (i % 100)
                    cfg.save_config()
                    i += 1
                    time.sleep(0.001)

            def reader():
                while not stop.is_set():
                    try:
                        cfg.reload_config()
                    except Exception as e:
                        stop.set()
                        raise

            t_w = threading.Thread(target=writer)
            t_r = threading.Thread(target=reader)
            t_w.start()
            t_r.start()
            time.sleep(0.2)
            stop.set()
            t_w.join()
            t_r.join()

            self.assertIsInstance(cfg.resolution[0], int)

    def test_save_config_without_path_raises(self):
        cfg = TuxemonConfig(config_path=None)
        cfg.config_model.display.resolution_x = 42
        with self.assertRaises(RuntimeError):
            cfg.save_config()

    def test_reload_config_when_file_removed_raises(self):
        with TemporaryDirectory() as td:
            td = Path(td)
            base = TuxemonFullConfig().model_dump()
            path = write_yaml(td, base)
            cfg = TuxemonConfig(config_path=path)
            path.unlink()
            with self.assertRaises(RuntimeError):
                cfg.reload_config()

    def test_logging_config_parsing_multiple_loggers(self):
        data = TuxemonFullConfig().model_dump()
        data["logging"] = {
            "loggers": "states.combat, event , neteria.client",
            "debug_logging": True,
            "debug_level": "info",
            "dump_to_file": False,
            "file_keep_max": 3,
        }
        model = TuxemonFullConfig.model_validate(data)
        log_cfg = LoggingConfig(model)
        self.assertIn("states.combat", log_cfg.loggers)
        self.assertIn("neteria.client", log_cfg.loggers)
        self.assertIn("event", log_cfg.loggers)

    def test_inputconfig_keyboard_mapping_respects_controls(self):
        base = TuxemonFullConfig().model_dump()
        base["controls"]["up"] = "w"
        base["controls"]["down"] = "s"
        model = TuxemonFullConfig.model_validate(base)
        input_cfg = InputConfig(model)

        self.assertIn(None, input_cfg.keyboard_button_map)
        if hasattr(pygame, "K_w"):
            self.assertIn(
                getattr(pygame, "K_w"), input_cfg.keyboard_button_map
            )

    def test_update_control_and_reload(self):
        with TemporaryDirectory() as td:
            td = Path(td)
            base = TuxemonFullConfig().model_dump()
            cfg_path = write_yaml(td, base)
            cfg = TuxemonConfig(config_path=cfg_path)

            cfg.update_control("up", pygame.K_w)
            self.assertEqual(
                cfg.config_model.controls.up, pygame.key.name(pygame.K_w)
            )
            cfg2 = TuxemonConfig(config_path=cfg_path)
            self.assertEqual(
                cfg2.config_model.controls.up, pygame.key.name(pygame.K_w)
            )
