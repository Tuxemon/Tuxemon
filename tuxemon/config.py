# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import configparser
from collections import OrderedDict
from collections.abc import Mapping
from typing import Any, Optional

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
        self.controller_overlay = cfg.getboolean(
            "display",
            "controller_overlay",
        )
        self.controller_transparency = cfg.getint(
            "display",
            "controller_transparency",
        )
        self.hide_mouse = cfg.getboolean("display", "hide_mouse")
        self.window_caption = cfg.get("display", "window_caption")

        # [game]
        self.data = cfg.get("game", "data")
        self.cli = cfg.getboolean("game", "cli_enabled")
        self.net_controller_enabled = cfg.getboolean(
            "game",
            "net_controller_enabled",
        )
        self.locale = cfg.get("game", "locale")
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

        # [player]
        self.player_animation_speed = cfg.getfloat("player", "animation_speed")
        self.player_npc = cfg.get("player", "player_npc")
        self.player_walkrate = cfg.getfloat("player", "player_walkrate")
        self.player_runrate = cfg.getfloat("player", "player_runrate")

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

        # input config (None means use default for the platform)
        self.gamepad_deadzone = 0.25
        self.gamepad_button_map = None
        self.keyboard_button_map = get_custom_pygame_keyboard_controls(cfg)

        # not configurable from the file yet
        self.mods = ["tuxemon"]


def get_custom_pygame_keyboard_controls(
    cfg: configparser.ConfigParser,
) -> Mapping[Optional[int], int]:
    """
    Parameters:
        cfg: Config parser.

    """
    import pygame.locals

    custom_controls: dict[Optional[int], int] = {None: events.UNICODE}
    for key, values in cfg.items("controls"):
        key = key.upper()
        button_value: Optional[int] = getattr(buttons, key, None)
        event_value: Optional[int] = getattr(events, key, None)
        for each in values.split(", "):
            # used in case of multiple keys assigned to 1 method
            # pygame.locals uses all caps for constants except for letters
            each = each.lower() if len(each) == 1 else each.upper()
            pygame_value: Optional[int] = getattr(
                pygame.locals, "K_" + each, None
            )
            if pygame_value is not None and button_value is not None:
                custom_controls[pygame_value] = button_value
            elif pygame_value is not None and event_value is not None:
                custom_controls[pygame_value] = event_value

    return custom_controls


def get_custom_pygame_keyboard_controls_names(
    cfg: configparser.ConfigParser,
) -> Mapping[Optional[str], int]:
    """
    Basically the same thing as `get_custom_pygame_keyboard_controls()`, but
    returns with the key's string value instead of int

    Parameters:
        cfg: Config parser.

    """
    custom_controls: dict[Optional[str], int] = {None: events.UNICODE}
    for key, values in cfg.items("controls"):
        key = key.upper()
        button_value: Optional[int] = getattr(buttons, key, None)
        event_value: Optional[int] = getattr(events, key, None)
        # used incase of multiple keys assigned to 1 method
        # pygame.locals uses all caps for constants except for letters
        for each in values.split(", "):
            each = each.lower() if len(each) == 1 else each.upper()
            if each is not None and button_value is not None:
                custom_controls[each] = button_value
            elif each is not None and event_value is not None:
                custom_controls[each] = event_value

    return custom_controls


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
