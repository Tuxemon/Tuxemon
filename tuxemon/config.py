# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Optional

import pygame
import yaml

from tuxemon.animation import Animation
from tuxemon.constants import paths
from tuxemon.platform.const import buttons, events

Animation.default_transition = "out_quint"


class TuxemonConfig:
    """
    Handles loading of the config file for the primary game and map editor.

    Do not forget to edit the default configuration specified below!
    """

    def __init__(self, config_path: Optional[str] = None) -> None:
        # Default configuration dictionary
        self.config = generate_default_config()
        self.config_path = config_path

        # Load customized configuration if the YAML file exists
        if config_path:
            try:
                with open(config_path) as yaml_file:
                    loaded_config = yaml.safe_load(yaml_file)

                    # Merge only existing sections while keeping defaults
                    for category, defaults in self.config.items():
                        if category in loaded_config:
                            defaults.update(loaded_config[category])

            except FileNotFoundError:
                # File does not exist; keep using defaults
                pass

        self.load_config()

        # Initialize other components
        self.input = InputConfig(self.config)
        self.controller = ControllerConfig(self.config)
        self.logging = LoggingConfig(self.config)
        self.locale = LocaleConfig(self.config)

        # not configurable from the file yet
        self.mods = ["tuxemon"]
        assert all(mod in paths.mods_subfolders for mod in self.mods)

    def save_config(self) -> None:
        """Saves the configuration to a YAML file."""
        if not self.config_path:
            raise RuntimeError("No path specified for saving configuration.")
        with open(self.config_path, "w") as yaml_file:
            yaml.dump(
                self.config, yaml_file, default_flow_style=False, indent=4
            )

    def load_config(self) -> None:
        # [display]
        display = self.config["display"]
        self.resolution: tuple[int, int] = (
            display["resolution_x"],
            display["resolution_y"],
        )
        self.splash: bool = display["splash"]
        self.fullscreen: bool = display["fullscreen"]
        self.fps: float = display["fps"]
        self.vsync: bool = display["vsync"]
        self.show_fps: bool = display["show_fps"]
        self.scaling: bool = display["scaling"]
        self.collision_map: bool = display["collision_map"]
        self.large_gui: bool = display["large_gui"]
        self.window_caption: str = display["window_caption"]

        # [game]
        game = self.config["game"]
        self.data: str = game["data"]
        self.cli: bool = game["cli_enabled"]
        self.net_controller_enabled: bool = game["net_controller_enabled"]
        self.dev_tools: bool = game["dev_tools"]
        self.recompile_translations: bool = game["recompile_translations"]
        self.skip_titlescreen: bool = game["skip_titlescreen"]
        self.compress_save: Optional[str] = game["compress_save"] or None

        # [gameplay]
        gameplay = self.config["gameplay"]
        self.items_consumed_on_failure: bool = gameplay[
            "items_consumed_on_failure"
        ]
        self.encounter_rate_modifier: float = gameplay[
            "encounter_rate_modifier"
        ]
        self.dialog_speed: str = gameplay["dialog_speed"]
        if self.dialog_speed not in ("slow", "max"):
            raise ValueError(
                "Invalid value for dialog_speed. Allowed: 'slow', 'max'"
            )
        self.unit_measure: str = gameplay["unit_measure"]
        if self.unit_measure not in ("metric", "imperial"):
            raise ValueError(
                "Invalid value for unit_measure. Allowed: 'metric', 'imperial'"
            )
        self.hemisphere: str = gameplay["hemisphere"]
        if self.hemisphere not in ("northern", "southern"):
            raise ValueError(
                "Invalid value for hemisphere. Allowed: 'northern', 'southern'"
            )

        sound_volume = float(gameplay["sound_volume"])
        self.sound_volume: float = max(0.0, min(sound_volume, 1.0))
        music_volume = float(gameplay["music_volume"])
        self.music_volume: float = max(0.0, min(music_volume, 1.0))

        # [player]
        player = self.config["player"]
        self.player_animation_speed: float = player["animation_speed"]
        self.player_npc: str = player["player_npc"]
        self.player_walkrate: float = player["player_walkrate"]
        self.player_runrate: float = player["player_runrate"]

    def reload_config(self) -> None:
        if not self.config_path:
            raise RuntimeError(
                "No path specified for reloading configuration."
            )

        with open(self.config_path) as yaml_file:
            self.config.update(yaml.safe_load(yaml_file))
        self.load_config()
        self.input.config = self.config
        self.input.reload_input_map()

    def update_attribute(
        self, section: str, attribute: str, value: str
    ) -> None:
        """
        Updates the attribute's value in the tuxemon.yaml.

        Parameters:
            section: the section (eg. gameplay)
            attribute: the attribute (eg. dialog_speed)
            value: the value (eg slow or max)
        """
        self.config[section][attribute] = value
        self.save_config()
        self.reload_config()

    def update_control(self, value: str, key: int) -> None:
        self.input.update_key(value, pygame.key.name(key))
        self.save_config()
        self.reload_config()

    def update_locale(self, value: str) -> None:
        self.config["game"]["locale"] = value
        self.locale.slug = value
        if value == "zh_CN":
            self.locale.font_file = "SourceHanSerifCN-Bold.otf"
        elif value == "ja":
            self.locale.font_file = "SourceHanSerifJP-Bold.otf"
        else:
            self.locale.font_file = "PressStart2P.ttf"
        self.config["game"]["language_font"] = self.locale.font_file
        self.save_config()
        self.reload_config()

    def reset_controls_to_default(self) -> None:
        self.input.reset_to_default()
        self.save_config()
        self.reload_config()


class ControllerConfig:
    """Handles controller-related configurations."""

    def __init__(self, config: dict[str, Any]) -> None:
        display = config["display"]
        self.overlay: bool = display["controller_overlay"]
        self.transparency: int = display["controller_transparency"]
        self.hide_mouse: bool = display["hide_mouse"]


class LocaleConfig:
    """Handles locale-related configurations."""

    def __init__(self, config: dict[str, Any]) -> None:
        game = config["game"]
        self.slug: str = game["locale"]
        self.translation_mode: str = game["translation_mode"]
        self.font_file: str = game["font_file"]


class InputConfig:
    """Handles input-related configurations."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.gamepad_deadzone: float = 0.25
        self.gamepad_button_map = None
        self.keyboard_button_map = self._get_custom_pygame_keyboard_controls()

    def _get_custom_pygame_keyboard_controls(
        self,
    ) -> Mapping[Optional[int], int]:
        """
        Returns a dictionary mapping pygame key constants to custom button values.
        """
        custom_controls: dict[Optional[int], int] = {None: events.UNICODE}
        for key, values in self.config["controls"].items():
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
        self.config["controls"][value] = key_name
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
            self.config["controls"][button] = key
        self.reload_input_map()


class LoggingConfig:
    """Handles logging-related configurations."""

    def __init__(self, config: dict[str, Any]) -> None:
        # [logging]
        # Log levels can be: debug, info, warning, error, or critical
        # Setting loggers to "all" will enable debug logging for all modules.
        #   Some available loggers:
        #     states.combat, states.world, event,
        #     neteria.server, neteria.client, neteria.core
        # Comma-separated list of which modules to enable logging on
        log = config["logging"]
        loggers_str: str = log["loggers"]
        self.loggers = loggers_str.replace(" ", "").split(",")
        self.debug_logging: bool = log["debug_logging"]
        self.debug_level: str = log["debug_level"]
        self.log_to_file: bool = log["dump_to_file"]
        self.log_keep_max: int = log["file_keep_max"]


def generate_default_config() -> dict[str, Any]:
    """
    Generate a config from defaults.

    When making game changes, do not forget to edit this config!

    Returns:
        Mapping of default values.
    """
    return {
        "display": {
            "resolution_x": 1280,
            "resolution_y": 720,
            "splash": True,
            "fullscreen": False,
            "fps": 60.0,
            "vsync": True,
            "show_fps": False,
            "scaling": True,
            "collision_map": False,
            "large_gui": False,
            "window_caption": "Tuxemon",
            "controller_overlay": False,
            "controller_transparency": 45,
            "hide_mouse": True,
        },
        "game": {
            "data": "tuxemon",
            "cli_enabled": False,
            "net_controller_enabled": False,
            "dev_tools": False,
            "recompile_translations": True,
            "skip_titlescreen": False,
            "compress_save": None,
            "locale": "en_US",
            "translation_mode": "none",
            "font_file": "PressStart2P.ttf",
            "language_font": "PressStart2P.ttf",
        },
        "gameplay": {
            "items_consumed_on_failure": True,
            "encounter_rate_modifier": 1.0,
            "dialog_speed": "slow",
            "unit_measure": "metric",
            "hemisphere": "northern",
            "sound_volume": 0.2,
            "music_volume": 0.5,
        },
        "player": {
            "animation_speed": 0.15,
            "player_npc": "npc_red",
            "player_walkrate": 3.75,
            "player_runrate": 7.35,
        },
        "controls": {
            "up": "up",
            "down": "down",
            "left": "left",
            "right": "right",
            "a": "return",
            "b": "rshift, lshift",
            "back": "escape",
            "backspace": "backspace",
        },
        "logging": {
            "loggers": "all",
            "debug_logging": True,
            "debug_level": "error",
            "dump_to_file": False,
            "file_keep_max": 5,
        },
    }
