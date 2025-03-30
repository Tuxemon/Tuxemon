# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import configparser
from collections import OrderedDict
from collections.abc import Mapping
from typing import Any, Optional

import pygame

from tuxemon.animation import Animation
from tuxemon.platform.const import buttons, events

Animation.default_transition = "out_quint"


class TuxemonConfig:
    """
    Handles loading of the config file for the primary game and map editor.

    Do not forget to edit the default configuration specified below!
    """

    def __init__(self, config_path: Optional[str] = None) -> None:
        # load default config
        cfg = generate_default_config()
        self.cfg = cfg
        self.config_path = config_path

        # update with customized values
        if config_path:
            cfg.read(config_path)

        # [display]
        resolution_x = cfg.getint("display", "resolution_x")
        resolution_y = cfg.getint("display", "resolution_y")
        self.resolution = resolution_x, resolution_y
        self.splash = cfg.getboolean("display", "splash")
        self.fullscreen = cfg.getboolean("display", "fullscreen")
        self.fps = cfg.getfloat("display", "fps")
        self.show_fps = cfg.getboolean("display", "show_fps")
        self.scaling = cfg.getboolean("display", "scaling")
        self.collision_map = cfg.getboolean("display", "collision_map")
        self.large_gui = cfg.getboolean("display", "large_gui")
        self.window_caption = cfg.get("display", "window_caption")

        # [game]
        self.data = cfg.get("game", "data")
        self.cli = cfg.getboolean("game", "cli_enabled")
        self.net_controller_enabled = cfg.getboolean(
            "game",
            "net_controller_enabled",
        )
        self.dev_tools = cfg.getboolean("game", "dev_tools")
        self.recompile_translations = cfg.getboolean(
            "game",
            "recompile_translations",
        )
        self.skip_titlescreen = cfg.getboolean("game", "skip_titlescreen")
        self.compress_save: Optional[str] = cfg.get("game", "compress_save")
        if self.compress_save == "None":
            self.compress_save = None

        # [gameplay]
        self.items_consumed_on_failure = cfg.getboolean(
            "gameplay",
            "items_consumed_on_failure",
        )
        self.encounter_rate_modifier = cfg.getfloat(
            "gameplay",
            "encounter_rate_modifier",
        )
        self.dialog_speed = cfg.get(
            "gameplay",
            "dialog_speed",
        )
        assert self.dialog_speed in ("slow", "max")
        self.unit_measure = cfg.get("gameplay", "unit_measure")
        assert self.unit_measure in ("metric", "imperial")
        self.hemisphere = cfg.get("gameplay", "hemisphere")
        assert self.hemisphere in ("northern", "southern")
        sound_volume = cfg.getfloat("gameplay", "sound_volume")
        self.sound_volume = max(0.0, min(sound_volume, 1.0))
        music_volume = cfg.getfloat("gameplay", "music_volume")
        self.music_volume = max(0.0, min(music_volume, 1.0))

        # [player]
        self.player_animation_speed = cfg.getfloat("player", "animation_speed")
        self.player_npc = cfg.get("player", "player_npc")
        self.player_walkrate = cfg.getfloat("player", "player_walkrate")
        self.player_runrate = cfg.getfloat("player", "player_runrate")

        self.input = InputConfig(self.cfg)
        self.controller = ControllerConfig(self.cfg)
        self.logging = LoggingConfig(cfg)
        self.locale = LocaleConfig(cfg)

        # not configurable from the file yet
        self.mods = ["tuxemon"]

    def save_config(self) -> None:
        assert self.config_path
        with open(self.config_path, "w") as fp:
            self.cfg.write(fp)

    def reload_config(self) -> None:
        assert self.config_path
        self.cfg.read(self.config_path)
        self.input.cfg = self.cfg
        self.input.reload_input_map()

    def update_attribute(
        self, section: str, attribute: str, value: str
    ) -> None:
        """
        Updates the attribute's value in the tuxemon.cfg.

        Parameters:
            section: the section (eg. gameplay)
            attribute: the attribute (eg. dialog_speed)
            value: the value (eg slow or max)
        """
        self.cfg.set(section, attribute, value)
        setattr(self, attribute, value)
        self.save_config()
        self.reload_config()

    def update_control(self, value: str, key: int) -> None:
        self.input.update_key(value, pygame.key.name(key))
        self.save_config()
        self.reload_config()

    def update_locale(self, value: str) -> None:
        self.cfg.set("game", "locale", value)
        self.locale.slug = value
        if value == "zh_CN":
            self.locale.font_file = "SourceHanSerifCN-Bold.otf"
        elif value == "ja":
            self.locale.font_file = "SourceHanSerifJP-Bold.otf"
        else:
            self.locale.font_file = "PressStart2P.ttf"
        self.cfg.set("game", "language_font", self.locale.font_file)
        self.save_config()
        self.reload_config()

    def reset_controls_to_default(self) -> None:
        self.input.reset_to_default()
        self.save_config()
        self.reload_config()


class ControllerConfig:
    """Handles controller-related configurations."""

    def __init__(self, cfg: configparser.ConfigParser) -> None:
        self.overlay = cfg.getboolean("display", "controller_overlay")
        self.transparency = cfg.getint("display", "controller_transparency")
        self.hide_mouse = cfg.getboolean("display", "hide_mouse")


class LocaleConfig:
    """Handles locale-related configurations."""

    def __init__(self, cfg: configparser.ConfigParser) -> None:
        self.slug = cfg.get("game", "locale")
        self.translation_mode = cfg.get("game", "translation_mode")
        self.font_file = cfg.get("game", "font_file")


class InputConfig:
    """Handles input-related configurations."""

    def __init__(self, cfg: configparser.ConfigParser) -> None:
        self.cfg = cfg
        self.gamepad_deadzone = 0.25
        self.gamepad_button_map = None
        self.keyboard_button_map = self._get_custom_pygame_keyboard_controls()

    def _get_custom_pygame_keyboard_controls(self) -> Mapping[int | None, int]:
        """
        Returns a dictionary mapping pygame key constants to custom button values.
        """
        custom_controls: dict[int | None, int] = {None: events.UNICODE}
        for key, values in self.cfg.items("controls"):
            key = key.upper()
            button_value: Optional[int] = getattr(buttons, key, None)
            event_value: Optional[int] = getattr(events, key, None)
            for each in values.split(", "):
                each = each.lower() if len(each) == 1 else each.upper()
                pygame_value: Optional[int] = getattr(
                    pygame, "K_" + each, None
                )
                if pygame_value is not None and button_value is not None:
                    custom_controls[pygame_value] = button_value
                elif pygame_value is not None and event_value is not None:
                    custom_controls[pygame_value] = event_value
        return custom_controls

    def update_key(self, value: str, key_name: str) -> None:
        self.cfg.set("controls", value, key_name)
        self.reload_input_map()

    def reload_input_map(self) -> None:
        self.keyboard_button_map = self._get_custom_pygame_keyboard_controls()

    def reset_to_default(self) -> None:
        default_controls = {
            "up": "up",
            "down": "down",
            "left": "left",
            "right": "right",
            "a": "return",
            "b": "rshift, lshift",
            "back": "escape",
            "backspace": "backspace",
        }
        for button, key in default_controls.items():
            self.cfg.set("controls", button, key)
        self.reload_input_map()


class LoggingConfig:
    """Handles logging-related configurations."""

    def __init__(self, cfg: configparser.ConfigParser) -> None:
        # [logging]
        # Log levels can be: debug, info, warning, error, or critical
        # Setting loggers to "all" will enable debug logging for all modules.
        #   Some available loggers:
        #     states.combat, states.world, event,
        #     neteria.server, neteria.client, neteria.core
        # Comma-separated list of which modules to enable logging on
        loggers_str = cfg.get("logging", "loggers")
        self.loggers = loggers_str.replace(" ", "").split(",")
        self.debug_logging = cfg.getboolean("logging", "debug_logging")
        self.debug_level = cfg.get("logging", "debug_level")
        self.log_to_file = cfg.getboolean("logging", "dump_to_file")
        self.log_keep_max = cfg.getint("logging", "file_keep_max")


def get_defaults() -> Mapping[str, Any]:
    """
    Generate a config from defaults.

    When making game changes, do not forget to edit this config!

    Returns:
        Mapping of default values.

    """
    return OrderedDict(
        (
            (
                "display",
                OrderedDict(
                    (
                        ("resolution_x", "1280"),
                        ("resolution_y", "720"),
                        ("splash", "True"),
                        ("fullscreen", "False"),
                        ("fps", "60"),
                        ("show_fps", "False"),
                        ("scaling", "True"),
                        ("collision_map", "False"),
                        ("large_gui", "False"),
                        ("controller_overlay", "False"),
                        ("controller_transparency", "45"),
                        ("hide_mouse", "True"),
                        ("window_caption", "Tuxemon"),
                    )
                ),
            ),
            (
                "game",
                OrderedDict(
                    (
                        ("data", "tuxemon"),
                        ("skip_titlescreen", "False"),
                        ("cli_enabled", "False"),
                        ("net_controller_enabled", "False"),
                        ("locale", "en_US"),
                        ("translation_mode", "none"),
                        ("font_file", "PressStart2P.ttf"),
                        ("dev_tools", "False"),
                        ("recompile_translations", "True"),
                        ("compress_save", "None"),
                    )
                ),
            ),
            (
                "gameplay",
                OrderedDict(
                    (
                        ("items_consumed_on_failure", "True"),
                        ("encounter_rate_modifier", "1.0"),
                        ("dialog_speed", "slow"),
                        ("unit_measure", "metric"),
                        ("hemisphere", "northern"),
                        ("sound_volume", "0.2"),
                        ("music_volume", "0.5"),
                    )
                ),
            ),
            (
                "player",
                OrderedDict(
                    (
                        ("animation_speed", "0.15"),
                        ("player_npc", "npc_red"),
                        ("player_walkrate", "3.75"),
                        ("player_runrate", "7.35"),
                    )
                ),
            ),
            (
                "logging",
                OrderedDict(
                    (
                        ("loggers", "all"),
                        ("debug_logging", "True"),
                        ("debug_level", "error"),
                        ("dump_to_file", "False"),
                        ("file_keep_max", "5"),
                    )
                ),
            ),
            (
                "controls",
                OrderedDict(
                    (
                        ("up", "up"),
                        ("down", "down"),
                        ("left", "left"),
                        ("right", "right"),
                        ("a", "return"),
                        ("b", "rshift, lshift"),
                        ("back", "escape"),
                        ("backspace", "backspace"),
                    )
                ),
            ),
        )
    )


def generate_default_config() -> configparser.ConfigParser:
    """Get new config file from defaults."""
    cfg = configparser.ConfigParser()
    cfg.read_dict(get_defaults())
    return cfg
