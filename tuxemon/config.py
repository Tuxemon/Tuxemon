# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import sys
import time
import warnings
from collections.abc import Mapping
from logging import FileHandler, Formatter, Logger, StreamHandler
from pathlib import Path
from typing import Any, Literal

import pygame
from pydantic import BaseModel, Field, ValidationError, field_validator

from tuxemon.animation import Animation
from tuxemon.constants import paths
from tuxemon.database.yaml_utils import dump_yaml_io, load_yaml
from tuxemon.platform.const import buttons, events

Animation.default_transition = "out_quint"

LOCALE_FONT_MAP = {
    "zh_CN": ("SourceHanSerifCN-Bold.otf", "SourceHanSerifCN-Bold.otf"),
    "ja": ("SourceHanSerifJP-Bold.otf", "SourceHanSerifJP-Bold.otf"),
    "default": ("PressStart2P.ttf", "Pizel.ttf"),
}


class DisplayConfig(BaseModel):
    """Configuration for the game display."""

    resolution_x: int = 1280
    resolution_y: int = 720
    splash: bool = True
    fullscreen: bool = False
    fps: float = 60.0
    vsync: bool = True
    show_fps: bool = False
    scaling: bool = True
    collision_map: bool = False
    large_gui: bool = False
    window_caption: str = "Tuxemon"


class GameConfig(BaseModel):
    """General game and system configuration."""

    data: str = "tuxemon"
    cli_enabled: bool = False
    net_controller_enabled: bool = False
    dev_tools: bool = False
    recompile_translations: bool = True
    skip_titlescreen: bool = False
    compress_save: str | None = None
    save_prefix: str = "slot"
    save_extension: str = "save"
    save_method: str = "json"
    save_slots: int = 6
    save_slots_per_page: int = 3
    locale: str = "en_US"
    translation_mode: str = "none"
    font_file: str = "PressStart2P.ttf"
    language_font: str = "PressStart2P.ttf"
    thin_font_file: str = "Pizel.ttf"
    minimal_font_file: str = "Minimal3x5.ttf"


class GameplayConfig(BaseModel):
    """Configuration for gameplay mechanics. Includes validation for volume and enums."""

    items_consumed_on_failure: bool = True
    encounter_rate_modifier: float = 1.0
    dialog_speed: Literal["slow", "medium", "fast", "max"] = "slow"
    unit_measure: Literal["metric", "imperial"] = "metric"
    hemisphere: Literal["northern", "southern"] = "northern"
    sound_volume: float = 0.2
    music_volume: float = 0.5
    combat_click_to_continue: bool = False

    @field_validator("sound_volume", "music_volume")
    def validate_volume(cls, v: float) -> float:
        return max(0.0, min(v, 1.0))


class GraphicsConfig(BaseModel):
    dialog_box_style: str = "default"
    menu_border: str = "gfx/borders/borders.png"
    menu_cursor: str = "gfx/arrow.png"
    menu_sound: str = "sound_menu_select"


class PlayerConfig(BaseModel):
    animation_speed: float = 0.15
    player_walkrate: float = 3.75
    player_runrate: float = 7.35


class ControlsConfig(BaseModel):
    up: str = "up"
    down: str = "down"
    left: str = "left"
    right: str = "right"
    a: str = "return"
    b: str = "rshift, lshift"
    back: str = "escape"
    backspace: str = "backspace"


class ControllerConfigModel(BaseModel):
    type: str | None = None
    overlay: bool = False
    transparency: int = 45
    hide_mouse: bool = True
    show_input_visualizer: bool = False
    combo_window_seconds: float = 5.0


class LoggingConfigModel(BaseModel):
    loggers: str = "all"
    debug_logging: bool = True
    debug_level: Literal["debug", "info", "warning", "error", "critical"] = (
        "error"
    )
    dump_to_file: bool = False
    file_keep_max: int = 5


class TuxemonFullConfig(BaseModel):
    display: DisplayConfig = Field(default_factory=DisplayConfig)
    game: GameConfig = Field(default_factory=GameConfig)
    gameplay: GameplayConfig = Field(default_factory=GameplayConfig)
    graphics: GraphicsConfig = Field(default_factory=GraphicsConfig)
    player: PlayerConfig = Field(default_factory=PlayerConfig)
    controls: ControlsConfig = Field(default_factory=ControlsConfig)
    controller: ControllerConfigModel = Field(
        default_factory=ControllerConfigModel
    )
    logging: LoggingConfigModel = Field(default_factory=LoggingConfigModel)


class TuxemonConfig:
    """
    Handles loading of the config file for the primary game and map editor,
    leveraging Pydantic for robust data validation.
    """

    config_model: TuxemonFullConfig

    def __init__(self, config_path: Path | None = None) -> None:
        self.config_path = config_path

        config_data: dict[str, Any] = TuxemonFullConfig().model_dump()

        if config_path and config_path.exists():
            loaded_config = load_yaml(config_path) or {}

            for category, defaults in config_data.items():
                if category in loaded_config and isinstance(defaults, dict):
                    defaults.update(loaded_config[category])
                elif category in loaded_config:
                    config_data[category] = loaded_config[category]

        # Validate merged config
        try:
            self.config_model = TuxemonFullConfig.model_validate(config_data)
        except ValidationError as e:
            print(
                f"Configuration validation failed. Falling back to defaults: {e}"
            )
            self.config_model = TuxemonFullConfig()

        self.input = InputConfig(self.config_model)
        self.logging = LoggingConfig(self.config_model)
        self.locale = LocaleConfig(self.config_model)
        self.controller = ControllerConfig(self.config_model)
        self.mods = ["tuxemon"]

    @property
    def resolution(self) -> tuple[int, int]:
        d = self.config_model.display
        return (d.resolution_x, d.resolution_y)

    @property
    def splash(self) -> bool:
        return self.config_model.display.splash

    @property
    def fullscreen(self) -> bool:
        return self.config_model.display.fullscreen

    @property
    def fps(self) -> float:
        return self.config_model.display.fps

    @property
    def vsync(self) -> bool:
        return self.config_model.display.vsync

    @property
    def show_fps(self) -> bool:
        return self.config_model.display.show_fps

    @property
    def scaling(self) -> bool:
        return self.config_model.display.scaling

    @property
    def collision_map(self) -> bool:
        return self.config_model.display.collision_map

    @property
    def large_gui(self) -> bool:
        return self.config_model.display.large_gui

    @property
    def window_caption(self) -> str:
        return self.config_model.display.window_caption

    @property
    def data(self) -> str:
        return self.config_model.game.data

    @property
    def cli(self) -> bool:
        return self.config_model.game.cli_enabled

    @property
    def net_controller_enabled(self) -> bool:
        return self.config_model.game.net_controller_enabled

    @property
    def dev_tools(self) -> bool:
        return self.config_model.game.dev_tools

    @property
    def recompile_translations(self) -> bool:
        return self.config_model.game.recompile_translations

    @property
    def skip_titlescreen(self) -> bool:
        return self.config_model.game.skip_titlescreen

    @property
    def compress_save(self) -> str | None:
        return self.config_model.game.compress_save

    @property
    def save_prefix(self) -> str:
        return self.config_model.game.save_prefix

    @property
    def save_slots(self) -> int:
        return self.config_model.game.save_slots

    @property
    def save_slots_per_page(self) -> int:
        return self.config_model.game.save_slots_per_page

    @property
    def save_extension(self) -> str:
        return self.config_model.game.save_extension

    @property
    def save_method(self) -> str:
        return self.config_model.game.save_method

    @property
    def items_consumed_on_failure(self) -> bool:
        return self.config_model.gameplay.items_consumed_on_failure

    @property
    def encounter_rate_modifier(self) -> float:
        return self.config_model.gameplay.encounter_rate_modifier

    @property
    def dialog_speed(self) -> str:
        return self.config_model.gameplay.dialog_speed

    @property
    def unit_measure(self) -> str:
        return self.config_model.gameplay.unit_measure

    @property
    def hemisphere(self) -> str:
        return self.config_model.gameplay.hemisphere

    @property
    def sound_volume(self) -> float:
        return self.config_model.gameplay.sound_volume

    @property
    def music_volume(self) -> float:
        return self.config_model.gameplay.music_volume

    @property
    def combat_click_to_continue(self) -> bool:
        return self.config_model.gameplay.combat_click_to_continue

    @property
    def dialog_box_style(self) -> str:
        return self.config_model.graphics.dialog_box_style

    @property
    def menu_border(self) -> str:
        return self.config_model.graphics.menu_border

    @property
    def menu_cursor(self) -> str:
        return self.config_model.graphics.menu_cursor

    @property
    def menu_sound(self) -> str:
        return self.config_model.graphics.menu_sound

    @property
    def animation_speed(self) -> float:
        return self.config_model.player.animation_speed

    @property
    def player_walkrate(self) -> float:
        return self.config_model.player.player_walkrate

    @property
    def player_runrate(self) -> float:
        return self.config_model.player.player_runrate

    def copy(self) -> TuxemonConfig:
        new = TuxemonConfig(config_path=self.config_path)
        new.config_model = self.config_model.model_copy(deep=True)

        new.input = InputConfig(new.config_model)
        new.logging = LoggingConfig(new.config_model)
        new.locale = LocaleConfig(new.config_model)
        new.controller = ControllerConfig(new.config_model)

        new.mods = list(self.mods)
        return new

    def save_config(self) -> None:
        """Saves the configuration from the Pydantic model to a YAML file."""
        if not self.config_path:
            raise RuntimeError("No path specified for saving configuration.")

        config_dict = self.config_model.model_dump()

        with self.config_path.open("w", encoding="utf-8") as yaml_file:
            dump_yaml_io(
                yaml_file,
                config_dict,
                default_flow_style=False,
                indent=4,
            )

    def reload_config(self) -> None:
        if not self.config_path or not self.config_path.exists():
            raise RuntimeError(
                "No path specified for reloading configuration."
            )

        loaded = load_yaml(self.config_path) or {}
        current = self.config_model.model_dump()

        for category, defaults in current.items():
            if category in loaded and isinstance(defaults, dict):
                defaults.update(loaded[category])
            elif category in loaded:
                current[category] = loaded[category]

        self.config_model = TuxemonFullConfig.model_validate(current)
        self.input = InputConfig(self.config_model)
        self.logging = LoggingConfig(self.config_model)
        self.locale = LocaleConfig(self.config_model)
        self.controller = ControllerConfig(self.config_model)

    def update_attribute(
        self,
        section: str,
        attribute: str,
        value: Any,
        save: bool = True,
    ) -> None:
        """
        Updates the attribute's value in the Pydantic model and saves/reloads.
        """
        sub_model = getattr(self.config_model, section)
        setattr(sub_model, attribute, value)

        # Special case: controls require keymap rebuild
        if section == "controls":
            self.input.reload_input_map()

        if save:
            self.save_config()

    def update_control(self, value: str, key: int) -> None:
        self.input.update_key(value, pygame.key.name(key))
        self.save_config()

    def update_locale(self, value: str) -> None:
        """
        Updates the locale and applies derived font logic.
        """
        self.config_model.game.locale = value

        font_file, thin_font = LOCALE_FONT_MAP.get(
            value, LOCALE_FONT_MAP["default"]
        )

        game = self.config_model.game
        game.language_font = font_file
        game.font_file = font_file
        game.thin_font_file = thin_font
        self.save_config()

    def reset_controls_to_default(self) -> None:
        self.config_model.controls = ControlsConfig()
        self.input.reload_input_map()
        self.save_config()


class ControllerConfig:
    """Reactive controller configuration wrapper."""

    def __init__(self, config_model: TuxemonFullConfig) -> None:
        self._model = config_model.controller

    @property
    def type(self) -> str | None:
        return self._model.type

    @property
    def overlay(self) -> bool:
        return self._model.overlay

    @property
    def transparency(self) -> int:
        return self._model.transparency

    @property
    def hide_mouse(self) -> bool:
        return self._model.hide_mouse

    @property
    def show_input_visualizer(self) -> bool:
        return self._model.show_input_visualizer

    @property
    def combo_window_seconds(self) -> float:
        return self._model.combo_window_seconds


class LocaleConfig:
    """Reactive locale configuration wrapper."""

    def __init__(self, config_model: TuxemonFullConfig) -> None:
        self._model = config_model.game

    @property
    def slug(self) -> str:
        return self._model.locale

    @property
    def translation_mode(self) -> str:
        return self._model.translation_mode

    @property
    def font_file(self) -> str:
        return self._model.font_file

    @property
    def thin_font_file(self) -> str:
        return self._model.thin_font_file

    @property
    def minimal_font_file(self) -> str:
        return self._model.minimal_font_file

class InputConfig:
    """Reactive input configuration wrapper with cached keymap."""

    def __init__(self, config_model: TuxemonFullConfig) -> None:
        self._model = config_model
        self._keyboard_button_map = self._build_keyboard_map()

    @property
    def controls(self) -> ControlsConfig:
        return self._model.controls

    @property
    def keyboard_button_map(self) -> Mapping[int | None, int]:
        return self._keyboard_button_map

    @staticmethod
    def normalize_key(value: int | str) -> int | None:
        # Already a keycode
        if isinstance(value, int):
            return value

        # Convert unicode like "w" → 119
        if isinstance(value, str) and len(value) == 1:
            try:
                return pygame.key.key_code(value)
            except ValueError:
                return None

        return None

    def _build_keyboard_map(self) -> Mapping[int | None, int]:
        """
        Builds the pygame key → internal button/event mapping.
        """
        custom_controls: dict[int | None, int] = {None: events.UNICODE}

        defaults = ControlsConfig().model_dump()
        raw = self.controls.model_dump()
        controls = {}

        for key, default_value in defaults.items():
            user_value = raw.get(key)
            controls[key] = user_value if user_value else default_value

        for key, values in controls.items():
            key = key.upper()
            button_value = getattr(buttons, key, None)
            event_value = getattr(events, key, None)
            internal_value = (
                button_value if button_value is not None else event_value
            )

            if internal_value is None:
                continue

            for each in values.split(", "):
                each = each.lower() if len(each) == 1 else each.upper()
                pygame_value = getattr(pygame, "K_" + each, None)
                if pygame_value is not None:
                    custom_controls[pygame_value] = internal_value

        return custom_controls

    def reload_input_map(self) -> None:
        """Rebuilds the derived keymap."""
        self._keyboard_button_map = self._build_keyboard_map()

    def update_key(self, value: str, key_name: str) -> None:
        """Updates a key binding and rebuilds the keymap."""
        setattr(self._model.controls, value, key_name)
        self.reload_input_map()

    def reset_to_default(self) -> None:
        """Resets controls to defaults and rebuilds keymap."""
        self._model.controls = ControlsConfig()
        self.reload_input_map()


class LoggingConfig:
    """Reactive logging configuration wrapper."""

    LOG_LEVELS = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }

    def __init__(self, config_model: TuxemonFullConfig):
        self._model = config_model.logging

    @property
    def loggers(self) -> list[str]:
        return self._model.loggers.replace(" ", "").split(",")

    @property
    def debug_logging(self) -> bool:
        return self._model.debug_logging

    @property
    def debug_level(self) -> str:
        return self._model.debug_level

    @property
    def log_to_file(self) -> bool:
        return self._model.dump_to_file

    @property
    def log_keep_max(self) -> int:
        return self._model.file_keep_max

    def configure(self) -> None:
        log_level = self.LOG_LEVELS.get(self.debug_level, logging.INFO)

        if self.debug_logging:
            warnings.filterwarnings("default")

        for logger_name in self.loggers:
            if logger_name == "all":
                print("Enabling logging of all modules.")
                logger = logging.getLogger()
            else:
                print(f"Enabling logging for module: {logger_name}")
                logger = logging.getLogger(logger_name)

            logger.setLevel(log_level)

            formatter = Formatter(
                "[%(asctime)s] %(name)s - %(levelname)s - %(message)s"
            )

            # Avoid duplicate stdout handlers
            if not any(
                isinstance(h, StreamHandler)
                and getattr(h, "stream", None) is sys.stdout
                for h in logger.handlers
            ):
                stream = StreamHandler(sys.stdout)
                stream.setLevel(log_level)
                stream.setFormatter(formatter)
                logger.addHandler(stream)

            if self.log_to_file:
                self._setup_file_logging(logger, formatter, log_level)

        logging.getLogger("orthographic").setLevel(logging.ERROR)

    def _setup_file_logging(
        self, logger: Logger, formatter: Formatter, log_level: int
    ) -> None:
        log_dir = paths.USER_STORAGE_DIR / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        timestamp = time.strftime("%Y-%m-%d_%Hh%Mm%Ss", time.localtime())
        file_path = log_dir / f"{timestamp}.log"

        # Avoid duplicate file handlers for the same file
        if not any(
            isinstance(h, FileHandler)
            and getattr(h, "baseFilename", None) == str(file_path)
            for h in logger.handlers
        ):
            fh = FileHandler(file_path)
            fh.setFormatter(formatter)
            fh.setLevel(log_level)
            logger.addHandler(fh)

        # Rotation: keep only the newest N files
        keep = max(1, self.log_keep_max)
        files = sorted(
            log_dir.glob("*.log"),
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )

        for old in files[keep:]:
            old.unlink(missing_ok=True)
