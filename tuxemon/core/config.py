#
# Tuxemon
# Copyright (C) 2014, William Edwards <shadowapex@gmail.com>,
#                     Benjamin Bean <superman2k5@gmail.com>
#
# This file is part of Tuxemon.
#
# Tuxemon is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Tuxemon is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Tuxemon.  If not, see <http://www.gnu.org/licenses/>.
#
# Contributor(s):
#
# William Edwards <shadowapex@gmail.com>
# Leif Theden <leif.theden@gmail.com>
#
#
# core.config Configuration parser.
#
#
"""
NOTE: REWRITE WHEN py2.7 SUPPORT IS DROPPED!
"""

from collections import OrderedDict

from six.moves import configparser

from tuxemon.core.animation import Animation
from tuxemon.core.platform.const import buttons, events

Animation.default_transition = 'out_quint'


class TuxemonConfig:
    """ Handles loading of the configuration file for the primary game and map editor.

    Do not forget to edit the default configuration specified below!
    """

    def __init__(self, config_path=None):
        # load default config
        cfg = generate_default_config()
        self.cfg = cfg

        # update with customized values
        if config_path:
            temp = configparser.ConfigParser()
            temp.read(config_path)
            populate_config(cfg, temp._sections)

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
        self.controller_overlay = cfg.getboolean("display", "controller_overlay")
        self.controller_transparency = cfg.getint("display", "controller_transparency")
        self.hide_mouse = cfg.getboolean("display", "hide_mouse")
        self.window_caption = cfg.get("display", "window_caption")

        # [sound]
        self.sound_volume = cfg.getfloat("sound", "sound_volume")
        self.music_volume = cfg.getfloat("sound", "music_volume")

        # [game]
        self.data = cfg.get("game", "data")
        self.starting_map = cfg.get("game", "starting_map")
        self.cli = cfg.getboolean("game", "cli_enabled")
        self.net_controller_enabled = cfg.getboolean("game", "net_controller_enabled")
        self.locale = cfg.get("game", "locale")
        self.dev_tools = cfg.getboolean("game", "dev_tools")
        self.recompile_translations = cfg.getboolean("game", "recompile_translations")
        
        # [gameplay]
        self.items_consumed_on_failure = cfg.getboolean("gameplay", "items_consumed_on_failure")
        self.encounter_rate_modifier = cfg.getfloat("gameplay", "encounter_rate_modifier")
        
        # [player]
        self.player_animation_speed = cfg.getfloat("player", "animation_speed")
        self.player_npc = cfg.get("player", "player_npc")
        self.player_walkrate = cfg.getfloat("player", "player_walkrate")  # tiles/second
        self.player_runrate = cfg.getfloat("player", "player_runrate")  # tiles/second

        # [logging]
        # Log levels can be: debug, info, warning, error, or critical
        # Setting loggers to "all" will enable debug logging for all modules.
        #   Some available loggers:
        #     core.states.combat, core.states.world, core.event,
        #     neteria.server, neteria.client, neteria.core
        # Comma-seperated list of which modules to enable logging on
        self.loggers = cfg.get("logging", "loggers")
        self.loggers = self.loggers.replace(" ", "").split(",")
        self.debug_logging = cfg.getboolean("logging", "debug_logging")
        self.debug_level = cfg.get("logging", "debug_level")

        # input config (None means use default for the platform)
        self.gamepad_deadzone = .25
        self.gamepad_button_map = None
        self.keyboard_button_map = get_custom_pygame_keyboard_controls(cfg);

        # not configurable from the file yet
        self.mods = ["tuxemon"]


def get_custom_pygame_keyboard_controls(cfg):
    import pygame.locals

    custom_controls = {None: events.UNICODE}
    for key, values in cfg.items("controls"):
        key = key.upper()   
        button_value = getattr(buttons, key, None)
        event_value = getattr(events, key, None)
        for each in values.split(", "):
            # pygame.locals uses all caps for constants except for letters
            each = each.lower() if len(each) == 1 else each.upper()
            pygame_value = getattr(pygame.locals, "K_"+each, None)
            if pygame_value is not None and button_value is not None:
                custom_controls[pygame_value] = button_value
            elif pygame_value is not None and event_value is not None:
                custom_controls[pygame_value] = event_value

    return custom_controls

def get_defaults():
    """ Generate a config from defaults

    When making game changes, do not forget to edit this config!

    :rtype: OrderedDict
    """
    return OrderedDict((
        ("display", OrderedDict((
            ("resolution_x", 1280),
            ("resolution_y", 720),
            ("splash", True),
            ("fullscreen", False),
            ("fps", 60),
            ("show_fps", False),
            ("scaling", True),
            ("collision_map", False),
            ("large_gui", False),
            ("controller_overlay", False),
            ("controller_transparency", 45),
            ("hide_mouse", True),
            ("window_caption", "Tuxemon"),
        ))),
        ("sound", OrderedDict((
            ("sound_volume", 1.0),
            ("music_volume", 1.0),
        ))),
        ("game", OrderedDict((
            ("data", "tuxemon"),
            ("starting_map", "player_house_bedroom.tmx"),
            ("cli_enabled", False),
            ("net_controller_enabled", False),
            ("locale", "en_US"),
            ("dev_tools", False),
            ("recompile_translations", False),
        ))),
        ("gameplay", OrderedDict((
            ("items_consumed_on_failure", True),
            ("encounter_rate_modifier", 1.0)
        ))),
        ("player", OrderedDict((
            ("animation_speed", 0.15),
            ("player_npc", "npc_red"),
            ("player_walkrate", 3.75),
            ("player_runrate", 7.35),
        ))),
        ("logging", OrderedDict((
            ("loggers", "all"),
            ("debug_logging", True),
            ("debug_level", "error")
        ))),
        ("controls", OrderedDict((
            ("up", "up"),
            ("down", "down"),
            ("left", "left"),
            ("right", "right"),
            ("a", "return"),
            ("b", "rshift, lshift"),
            ("back", "escape"),
            ("backspace", "backspace")
        ))),
    ))


def generate_default_config():
    """ Get new config file from defaults

    :rtype: configparser.ConfigParser
    """
    cfg = configparser.ConfigParser()
    populate_config(cfg, get_defaults())
    return cfg


def populate_config(config, data):
    """ Workaround awful configparser defaults.

    :type data: dict
    :return:
    """
    # ConfigParser py2.7 'defaults' is absolutely braindead, half-baked, dumb.  WTF's all over.
    # so we fill in values manually, because they won't be read or written otherwise.
    for k, v in data.items():
        try:
            config.add_section(k)
        except configparser.DuplicateSectionError:
            pass
        for option, value in v.items():
            config.set(k, option, str(value))  # yes.  all values must be stored as a string
