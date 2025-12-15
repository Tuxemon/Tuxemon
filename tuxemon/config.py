# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any, Literal, Optional

import pygame
import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator

from tuxemon.animation import Animation
from tuxemon.platform.const import buttons, events

Animation.default_transition = "out_quint"


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
    compress_save: Optional[str] = None
    save_prefix: str = "slot"
    save_extension: str = "save"
    save_method: str = "json"
    locale: str = "en_US"
    translation_mode: str = "none"
    font_file: str = "PressStart2P.ttf"
    language_font: str = "PressStart2P.ttf"
    thin_font_file: str = "Pizel.ttf"


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
    type: Optional[str] = None
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

    def __init__(self, config_path: Optional[Path] = None) -> None:
        self.config_path = config_path

        config_data: dict[str, Any] = TuxemonFullConfig().model_dump()

        if config_path and config_path.exists():
            with config_path.open() as yaml_file:
                loaded_config = yaml.safe_load(yaml_file) or {}

            for category, defaults in config_data.items():
                if category in loaded_config and isinstance(defaults, dict):
                    defaults.update(loaded_config[category])
                elif category in loaded_config:
                    config_data[category] = loaded_config[category]

        try:
            self.config_model = TuxemonFullConfig.model_validate(config_data)
        except ValidationError as e:
            print(
                f"Configuration validation failed. Falling back to defaults: {e}"
            )
            self.config_model = (
                TuxemonFullConfig()
            )  # Fallback to clean defaults

        self.load_config_attributes()

        self.input: InputConfig = InputConfig(self.config_model)
        self.logging: LoggingConfig = LoggingConfig(self.config_model)
        self.locale: LocaleConfig = LocaleConfig(self.config_model)
        self.controller: ControllerConfig = ControllerConfig(self.config_model)
        self.mods = ["tuxemon"]

    def save_config(self) -> None:
        """Saves the configuration from the Pydantic model to a YAML file."""
        if not self.config_path:
            raise RuntimeError("No path specified for saving configuration.")

        config_dict = self.config_model.model_dump()

        with self.config_path.open("w") as yaml_file:
            yaml.dump(
                config_dict, yaml_file, default_flow_style=False, indent=4
            )

    def load_config_attributes(self) -> None:
        """Assigns Pydantic model values to easy-access instance attributes."""
        # [display]
        display = self.config_model.display
        self.resolution = (
            display.resolution_x,
            display.resolution_y,
        )
        self.splash = display.splash
        self.fullscreen = display.fullscreen
        self.fps = display.fps
        self.vsync = display.vsync
        self.show_fps = display.show_fps
        self.scaling = display.scaling
        self.collision_map = display.collision_map
        self.large_gui = display.large_gui
        self.window_caption = display.window_caption

        # [game]
        game = self.config_model.game
        self.data = game.data
        self.cli = game.cli_enabled
        self.net_controller_enabled = game.net_controller_enabled
        self.dev_tools = game.dev_tools
        self.recompile_translations = game.recompile_translations
        self.skip_titlescreen = game.skip_titlescreen
        self.compress_save = game.compress_save
        self.save_prefix = game.save_prefix
        self.save_extension = game.save_extension
        self.save_method = game.save_method

        # [gameplay]
        gameplay = self.config_model.gameplay
        self.items_consumed_on_failure = gameplay.items_consumed_on_failure
        self.encounter_rate_modifier = gameplay.encounter_rate_modifier

        self.dialog_speed = gameplay.dialog_speed
        self.unit_measure = gameplay.unit_measure
        self.hemisphere = gameplay.hemisphere

        self.sound_volume = gameplay.sound_volume
        self.music_volume = gameplay.music_volume
        self.combat_click_to_continue = gameplay.combat_click_to_continue

        # [graphics]
        graphics = self.config_model.graphics
        self.dialog_box_style = graphics.dialog_box_style
        self.menu_border = graphics.menu_border
        self.menu_cursor = graphics.menu_cursor
        self.menu_sound = graphics.menu_sound

        # [player]
        player = self.config_model.player
        self.animation_speed = player.animation_speed
        self.player_walkrate = player.player_walkrate
        self.player_runrate = player.player_runrate

    def reload_config(self) -> None:
        if not self.config_path or not self.config_path.exists():
            raise RuntimeError(
                "No path specified for reloading configuration."
            )

        with self.config_path.open() as yaml_file:
            loaded_config = yaml.safe_load(yaml_file) or {}

        current_config = self.config_model.model_dump()
        for category, defaults in current_config.items():
            if category in loaded_config and isinstance(defaults, dict):
                defaults.update(loaded_config[category])
            elif category in loaded_config:
                current_config[category] = loaded_config[category]

        self.config_model = TuxemonFullConfig.model_validate(current_config)

        self.load_config_attributes()

        self.input.reload_input_map()
        self.locale.slug = self.config_model.game.locale
        self.locale.translation_mode = self.config_model.game.translation_mode
        self.locale.font_file = self.config_model.game.language_font
        self.locale.thin_font_file = self.config_model.game.thin_font_file

    def update_attribute(
        self, section: str, attribute: str, value: Any
    ) -> None:
        """
        Updates the attribute's value in the Pydantic model and saves/reloads.
        """
        sub_model = getattr(self.config_model, section)
        setattr(sub_model, attribute, value)
        self.save_config()
        self.reload_config()

    def update_control(self, value: str, key: int) -> None:
        self.input.update_key(value, pygame.key.name(key))
        self.save_config()
        self.reload_config()

    def update_locale(self, value: str) -> None:
        """Handles locale update and derived font file changes."""

        # Set the base locale value on the Pydantic model
        self.config_model.game.locale = value

        # Apply the derived font logic
        if value == "zh_CN":
            font_file = "SourceHanSerifCN-Bold.otf"
            thin_font = "SourceHanSerifCN-Bold.otf"
        elif value == "ja":
            font_file = "SourceHanSerifJP-Bold.otf"
            thin_font = "SourceHanSerifJP-Bold.otf"
        else:
            font_file = "PressStart2P.ttf"
            thin_font = "Pizel.ttf"

        # Update the font attributes on the Pydantic model
        self.config_model.game.language_font = font_file
        self.config_model.game.font_file = font_file
        self.config_model.game.thin_font_file = thin_font

        self.save_config()
        self.reload_config()

    def reset_controls_to_default(self) -> None:
        self.input.reset_to_default()
        self.save_config()
        self.reload_config()


class ControllerConfig:
    """Handles controller-related configurations."""

    def __init__(self, config_model: TuxemonFullConfig) -> None:
        controller = config_model.controller
        self.type = controller.type
        self.overlay = controller.overlay
        self.transparency = controller.transparency
        self.hide_mouse = controller.hide_mouse
        self.show_input_visualizer = controller.show_input_visualizer
        self.combo_window_seconds = controller.combo_window_seconds


class LocaleConfig:
    """Handles locale-related configurations."""

    def __init__(self, config_model: TuxemonFullConfig) -> None:
        game = config_model.game
        self.slug = game.locale
        self.translation_mode = game.translation_mode
        self.font_file = game.font_file
        self.thin_font_file = game.thin_font_file


class InputConfig:
    """Handles input-related configurations."""

    def __init__(self, config_model: TuxemonFullConfig) -> None:
        self.config_model = config_model
        self.keyboard_button_map = self._get_custom_pygame_keyboard_controls()

    def _get_custom_pygame_keyboard_controls(
        self,
    ) -> Mapping[Optional[int], int]:
        """
        Returns a dictionary mapping pygame key constants to custom button values.
        """
        custom_controls: dict[Optional[int], int] = {None: events.UNICODE}

        for key, values in self.config_model.controls.model_dump().items():
            key = key.upper()
            button_value: Optional[int] = getattr(buttons, key, None)
            event_value: Optional[int] = getattr(events, key, None)

            internal_value = (
                button_value if button_value is not None else event_value
            )
            if internal_value is None:
                continue

            for each in values.split(", "):
                each = each.lower() if len(each) == 1 else each.upper()
                pygame_value: Optional[int] = getattr(
                    pygame, "K_" + each, None
                )
                if pygame_value is not None:
                    custom_controls[pygame_value] = internal_value

        return custom_controls

    def update_key(self, value: str, key_name: str) -> None:
        """Updates a key binding on the Pydantic controls model."""
        setattr(self.config_model.controls, value, key_name)
        self.reload_input_map()

    def reload_input_map(self) -> None:
        self.keyboard_button_map = self._get_custom_pygame_keyboard_controls()

    def reset_to_default(self) -> None:
        """Resets the controls section to the defaults defined in the ControlsConfig model."""
        self.config_model.controls = ControlsConfig()
        self.reload_input_map()


class LoggingConfig:
    """Handles logging-related configurations."""

    def __init__(self, config_model: TuxemonFullConfig) -> None:
        # [logging]
        # Log levels can be: debug, info, warning, error, or critical
        # Setting loggers to "all" will enable debug logging for all modules.
        #   Some available loggers:
        #     states.combat, states.world, event,
        #     neteria.server, neteria.client, neteria.core
        # Comma-separated list of which modules to enable logging on
        log = config_model.logging
        loggers_str: str = log.loggers
        self.loggers = loggers_str.replace(" ", "").split(",")
        self.debug_logging = log.debug_logging
        self.debug_level = log.debug_level
        self.log_to_file = log.dump_to_file
        self.log_keep_max = log.file_keep_max
