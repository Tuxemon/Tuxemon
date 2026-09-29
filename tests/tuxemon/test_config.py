# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import io
import threading
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

import pygame
import pytest
import yaml

from tuxemon.config import (
    ControllerConfig,
    ControlsConfig,
    InputConfig,
    LocaleConfig,
    LoggingConfig,
    TuxemonConfig,
    TuxemonFullConfig,
)
from tuxemon.database.yaml_utils import dump_yaml_path
from tuxemon.platform.const import buttons


def write_yaml(dir_path: Path, data) -> Path:
    p = dir_path / "tuxemon.yaml"
    dump_yaml_path(p, data)
    return p


def test_defaults_load_when_no_file():
    cfg = TuxemonConfig(config_path=None)
    assert cfg.config_model is not None
    assert cfg.resolution == (1280, 720)
    assert cfg.dialog_speed == "slow"


def test_load_partial_yaml_merges_with_defaults():
    with TemporaryDirectory() as td:
        td = Path(td)
        partial = {
            "display": {"resolution_x": 800},
            "gameplay": {"music_volume": 0.75},
        }
        path = write_yaml(td, partial)
        cfg = TuxemonConfig(config_path=path)

        assert cfg.resolution[0] == 800
        assert cfg.music_volume == pytest.approx(0.75)
        assert cfg.resolution[1] == 720
        assert cfg.dialog_speed == "slow"


def test_invalid_enum_falls_back_to_defaults_and_reports():
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
        assert "Configuration validation failed" in output
        assert cfg.dialog_speed == "slow"
        assert cfg.fps == 60.0


def test_volume_clamping_and_validation():
    data = TuxemonFullConfig().model_dump()
    data["gameplay"]["sound_volume"] = -1.0
    data["gameplay"]["music_volume"] = 2.0

    model = TuxemonFullConfig.model_validate(data)

    assert model.gameplay.sound_volume == 0.0
    assert model.gameplay.music_volume == 1.0


def test_update_locale_writes_font_fields():
    with TemporaryDirectory() as td:
        td = Path(td)
        base = TuxemonFullConfig().model_dump()
        cfg_path = write_yaml(td, base)
        cfg = TuxemonConfig(config_path=cfg_path)

        cfg.update_locale("zh_CN")
        assert cfg.config_model.game.locale == "zh_CN"
        assert "SourceHanSerifCN" in cfg.config_model.game.font_file
        assert "SourceHanSerifCN" in cfg.config_model.game.thin_font_file

        cfg.update_locale("ja")
        assert "SourceHanSerifJP" in cfg.config_model.game.font_file

        cfg.update_locale("en_US")
        assert cfg.config_model.game.font_file == "PressStart2P.ttf"


def test_reset_controls_to_default():
    with TemporaryDirectory() as td:
        td = Path(td)
        base = TuxemonFullConfig().model_dump()
        cfg_path = write_yaml(td, base)
        cfg = TuxemonConfig(config_path=cfg_path)

        cfg.input.update_key("up", "w")
        assert cfg.config_model.controls.up == "w"

        cfg.reset_controls_to_default()
        assert cfg.config_model.controls == ControlsConfig()
        assert None in cfg.input.keyboard_button_map


def test_reload_config_applies_changes():
    with TemporaryDirectory() as td:
        td = Path(td)
        base = TuxemonFullConfig().model_dump()
        path = write_yaml(td, base)
        cfg = TuxemonConfig(config_path=path)

        new = base.copy()
        new["display"]["resolution_x"] = 640
        path.write_text(yaml.safe_dump(new))

        cfg.reload_config()
        assert cfg.resolution[0] == 640


def test_save_load_roundtrip_full():
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
        assert cfg2.config_model.display.resolution_x == 999
        assert cfg2.config_model.game.locale == "ja"
        assert cfg2.config_model.gameplay.sound_volume == pytest.approx(0.33)
        assert cfg2.config_model.graphics.menu_sound == "new_sound"
        assert cfg2.config_model.player.player_runrate == pytest.approx(9.99)


def test_concurrent_read_write_race():
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
                except Exception:
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

        assert isinstance(cfg.resolution[0], int)


def test_save_config_without_path_raises():
    cfg = TuxemonConfig(config_path=None)
    cfg.config_model.display.resolution_x = 42

    with pytest.raises(RuntimeError):
        cfg.save_config()


def test_reload_config_when_file_removed_raises():
    with TemporaryDirectory() as td:
        td = Path(td)
        base = TuxemonFullConfig().model_dump()
        path = write_yaml(td, base)
        cfg = TuxemonConfig(config_path=path)

        path.unlink()

        with pytest.raises(RuntimeError):
            cfg.reload_config()


def test_logging_config_parsing_multiple_loggers():
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

    assert "states.combat" in log_cfg.loggers
    assert "event" in log_cfg.loggers
    assert "neteria.client" in log_cfg.loggers


def test_inputconfig_keyboard_mapping_respects_controls():
    base = TuxemonFullConfig().model_dump()
    base["controls"]["up"] = "w"
    base["controls"]["down"] = "s"

    model = TuxemonFullConfig.model_validate(base)
    input_cfg = InputConfig(model)

    assert None in input_cfg.keyboard_button_map

    if hasattr(pygame, "K_w"):
        assert getattr(pygame, "K_w") in input_cfg.keyboard_button_map


def test_update_control_and_reload():
    with TemporaryDirectory() as td:
        td = Path(td)
        base = TuxemonFullConfig().model_dump()
        cfg_path = write_yaml(td, base)
        cfg = TuxemonConfig(config_path=cfg_path)

        cfg.update_control("up", pygame.K_w)
        assert cfg.config_model.controls.up == pygame.key.name(pygame.K_w)

        cfg2 = TuxemonConfig(config_path=cfg_path)
        assert cfg2.config_model.controls.up == pygame.key.name(pygame.K_w)


def test_inputconfig_never_diverges_from_model_controls():
    base = TuxemonFullConfig().model_dump()
    model = TuxemonFullConfig.model_validate(base)
    input_cfg = InputConfig(model)

    model.controls.up = "w"
    model.controls.down = "s"

    input_cfg.reload_input_map()
    if hasattr(pygame, "K_w"):
        assert getattr(pygame, "K_w") in input_cfg.keyboard_button_map
    if hasattr(pygame, "K_s"):
        assert getattr(pygame, "K_s") in input_cfg.keyboard_button_map


def test_reset_controls_updates_model_and_keymap():
    with TemporaryDirectory() as td:
        td = Path(td)
        base = TuxemonFullConfig().model_dump()
        cfg_path = write_yaml(td, base)
        cfg = TuxemonConfig(config_path=cfg_path)
        cfg.input.update_key("up", "w")

        assert cfg.config_model.controls.up == "w"

        cfg.reset_controls_to_default()

        assert cfg.config_model.controls == ControlsConfig()
        assert None in cfg.input.keyboard_button_map


def test_locale_wrapper_reflects_model_changes():
    base = TuxemonFullConfig().model_dump()
    model = TuxemonFullConfig.model_validate(base)
    locale_cfg = LocaleConfig(model)

    assert locale_cfg.slug == "en_US"
    assert "PressStart2P" in locale_cfg.font_file

    model.game.locale = "ja"
    model.game.font_file = "SourceHanSerifJP-Bold.otf"
    model.game.thin_font_file = "SourceHanSerifJP-Bold.otf"

    assert locale_cfg.slug == "ja"
    assert "SourceHanSerifJP" in locale_cfg.font_file
    assert "SourceHanSerifJP" in locale_cfg.thin_font_file


def test_controller_wrapper_reflects_model_changes():
    base = TuxemonFullConfig().model_dump()
    model = TuxemonFullConfig.model_validate(base)
    controller_cfg = ControllerConfig(model)

    assert controller_cfg.overlay is False

    model.controller.overlay = True
    model.controller.combo_window_seconds = 7.5

    assert controller_cfg.overlay is True
    assert controller_cfg.combo_window_seconds == 7.5


def test_logging_wrapper_reflects_model_changes():
    base = TuxemonFullConfig().model_dump()
    base["logging"]["loggers"] = "states.world, event"
    model = TuxemonFullConfig.model_validate(base)
    log_cfg = LoggingConfig(model)

    assert "states.world" in log_cfg.loggers
    assert "event" in log_cfg.loggers

    model.logging.loggers = "states.combat, neteria.client"
    assert "states.combat" in log_cfg.loggers
    assert "neteria.client" in log_cfg.loggers


def test_reload_config_preserves_non_overridden_fields():
    with TemporaryDirectory() as td:
        td = Path(td)
        base = TuxemonFullConfig().model_dump()
        base["display"]["resolution_x"] = 800
        cfg_path = write_yaml(td, base)

        cfg = TuxemonConfig(config_path=cfg_path)
        assert cfg.resolution[0] == 800

        updated = {"display": {"resolution_x": 1024}}
        cfg_path.write_text(yaml.safe_dump(updated))

        cfg.reload_config()
        assert cfg.resolution[0] == 1024
        assert cfg.resolution[1] == 720


def test_reload_config_rebuilds_input_map_after_controls_change():
    with TemporaryDirectory() as td:
        td = Path(td)
        base = TuxemonFullConfig().model_dump()
        cfg_path = write_yaml(td, base)

        cfg = TuxemonConfig(config_path=cfg_path)

        updated = base.copy()
        updated["controls"] = {
            "up": "w",
            "down": "down",
            "left": "left",
            "right": "right",
            "a": "return",
            "b": "rshift, lshift",
            "back": "escape",
            "backspace": "backspace",
        }
        cfg_path.write_text(yaml.safe_dump(updated))

        cfg.reload_config()

        assert cfg.config_model.controls.up == "w"

        if hasattr(pygame, "K_w"):
            assert getattr(pygame, "K_w") in cfg.input.keyboard_button_map


def test_reload_config_does_not_break_wrappers():
    with TemporaryDirectory() as td:
        td = Path(td)
        base = TuxemonFullConfig().model_dump()
        cfg_path = write_yaml(td, base)

        cfg = TuxemonConfig(config_path=cfg_path)

        updated = base.copy()
        updated["game"] = {
            "locale": "ja",
            "font_file": "SourceHanSerifJP-Bold.otf",
            "thin_font_file": "SourceHanSerifJP-Bold.otf",
            "data": "tuxemon",
            "cli_enabled": False,
            "net_controller_enabled": False,
            "dev_tools": False,
            "recompile_translations": True,
            "skip_titlescreen": False,
            "compress_save": None,
            "save_prefix": "slot",
            "save_extension": "save",
            "save_method": "json",
            "translation_mode": "none",
            "language_font": "SourceHanSerifJP-Bold.otf",
        }
        cfg_path.write_text(yaml.safe_dump(updated))

        cfg.reload_config()

        assert cfg.locale.slug == "ja"
        assert "SourceHanSerifJP" in cfg.locale.font_file


def test_reload_config_keeps_controller_wrapper_in_sync():
    with TemporaryDirectory() as td:
        td = Path(td)
        base = TuxemonFullConfig().model_dump()
        cfg_path = write_yaml(td, base)

        cfg = TuxemonConfig(config_path=cfg_path)

        updated = base.copy()
        updated["controller"]["overlay"] = True
        updated["controller"]["combo_window_seconds"] = 9.0
        cfg_path.write_text(yaml.safe_dump(updated))

        cfg.reload_config()

        assert cfg.controller.overlay is True
        assert cfg.controller.combo_window_seconds == 9.0


def test_reload_config_rebuilds_all_wrappers():
    with TemporaryDirectory() as td:
        td = Path(td)
        base = TuxemonFullConfig().model_dump()
        cfg_path = write_yaml(td, base)

        cfg = TuxemonConfig(config_path=cfg_path)

        old_input = cfg.input
        old_locale = cfg.locale
        old_controller = cfg.controller
        old_logging = cfg.logging
        old_model = cfg.config_model

        updated = base.copy()
        updated["display"]["resolution_x"] = 777
        cfg_path.write_text(yaml.safe_dump(updated))

        cfg.reload_config()

        assert cfg.config_model is not old_model
        assert cfg.input is not old_input
        assert cfg.locale is not old_locale
        assert cfg.controller is not old_controller
        assert cfg.logging is not old_logging
        assert cfg.input._model is cfg.config_model
        assert cfg.locale._model is cfg.config_model.game
        assert cfg.controller._model is cfg.config_model.controller
        assert cfg.logging._model is cfg.config_model.logging


def test_normalize_key():
    assert InputConfig.normalize_key(119) == 119  # already keycode
    assert InputConfig.normalize_key("w") == pygame.key.key_code("w")
    assert InputConfig.normalize_key("W") == pygame.key.key_code("w")
    assert InputConfig.normalize_key("invalid") is None
    assert InputConfig.normalize_key("") is None
    assert InputConfig.normalize_key("ab") is None


def test_build_keyboard_map_defaults():
    model = TuxemonFullConfig()
    input_cfg = InputConfig(model)
    assert None in input_cfg.keyboard_button_map
    assert pygame.K_UP in input_cfg.keyboard_button_map
    assert input_cfg.keyboard_button_map[pygame.K_UP] == buttons.UP


def test_build_keyboard_map_custom_controls():
    base = TuxemonFullConfig().model_dump()
    base["controls"]["up"] = "w"
    base["controls"]["a"] = "return"
    model = TuxemonFullConfig.model_validate(base)
    input_cfg = InputConfig(model)
    assert pygame.K_w in input_cfg.keyboard_button_map
    assert input_cfg.keyboard_button_map[pygame.K_w] == buttons.UP
    assert pygame.K_RETURN in input_cfg.keyboard_button_map
    assert input_cfg.keyboard_button_map[pygame.K_RETURN] == buttons.A


def test_reload_input_map_rebuilds():
    base = TuxemonFullConfig().model_dump()
    model = TuxemonFullConfig.model_validate(base)
    input_cfg = InputConfig(model)
    old_map = dict(input_cfg.keyboard_button_map)
    model.controls.up = "w"
    input_cfg.reload_input_map()
    assert input_cfg.keyboard_button_map != old_map
    assert pygame.K_w in input_cfg.keyboard_button_map


def test_update_key_updates_model_and_map():
    base = TuxemonFullConfig().model_dump()
    model = TuxemonFullConfig.model_validate(base)
    input_cfg = InputConfig(model)
    input_cfg.update_key("up", "w")
    assert model.controls.up == "w"
    assert pygame.K_w in input_cfg.keyboard_button_map


def test_reset_to_default():
    base = TuxemonFullConfig().model_dump()
    model = TuxemonFullConfig.model_validate(base)
    input_cfg = InputConfig(model)
    input_cfg.update_key("up", "w")
    assert model.controls.up == "w"
    input_cfg.reset_to_default()
    assert model.controls == ControlsConfig()
    assert pygame.K_UP in input_cfg.keyboard_button_map
    assert None in input_cfg.keyboard_button_map


def test_copy_produces_independent_model():
    base = TuxemonFullConfig().model_dump()
    model = TuxemonFullConfig.model_validate(base)
    cfg = TuxemonConfig(config_path=None)
    cfg.config_model = model
    new = cfg.copy()
    assert new.config_model is not cfg.config_model
    cfg.config_model.display.resolution_x = 999
    assert new.config_model.display.resolution_x != 999


def test_copy_rebuilds_all_wrappers():
    cfg = TuxemonConfig(config_path=None)
    old_input = cfg.input
    old_locale = cfg.locale
    old_controller = cfg.controller
    old_logging = cfg.logging
    new = cfg.copy()
    assert new.input is not old_input
    assert new.locale is not old_locale
    assert new.controller is not old_controller
    assert new.logging is not old_logging
    assert new.input._model is new.config_model
    assert new.locale._model is new.config_model.game
    assert new.controller._model is new.config_model.controller
    assert new.logging._model is new.config_model.logging


def test_copy_preserves_mods_list_but_not_reference():
    cfg = TuxemonConfig(config_path=None)
    cfg.mods.append("extra_mod")
    new = cfg.copy()
    assert new.mods == cfg.mods
    assert new.mods is not cfg.mods


def test_copy_rebuilds_input_map():
    cfg = TuxemonConfig(config_path=None)
    cfg.config_model.controls.up = "w"
    cfg.input.reload_input_map()
    new = cfg.copy()

    if hasattr(pygame, "K_w"):
        assert getattr(pygame, "K_w") in new.input.keyboard_button_map

    assert new.input.keyboard_button_map is not cfg.input.keyboard_button_map


def test_copy_does_not_mutate_original():
    cfg = TuxemonConfig(config_path=None)
    new = cfg.copy()
    new.config_model.display.resolution_x = 555
    assert cfg.config_model.display.resolution_x != 555
