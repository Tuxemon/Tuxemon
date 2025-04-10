# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional, no_type_check

from tuxemon import log, prepare
from tuxemon.session import local_session

if TYPE_CHECKING:
    from pygame.surface import Surface

    from tuxemon.client import LocalPygameClient
    from tuxemon.config import TuxemonConfig

logger = logging.getLogger(__name__)


def main(load_slot: Optional[int] = None) -> None:
    """
    Configure and start the game.

    Add all available states to our scene manager (:class:`tools.Client`)
    and start the game using the pygame interface.

    Parameters:
        load_slot: Number of the save slot to load, if any.

    """
    log.configure()
    prepare.init()
    config = prepare.CONFIG
    screen = prepare.SCREEN

    import pygame

    client = initialize_client(config, screen)

    # global/singleton hack for now
    setattr(prepare, "GLOBAL_CONTROL", client)
    # WIP.  Will be more complete with game-view
    local_session.client = client

    configure_game_states(client, config, load_slot)

    if config.collision_map:
        configure_debug_options(client)

    client.main()
    pygame.quit()


def initialize_client(
    config: TuxemonConfig, screen: Surface
) -> LocalPygameClient:
    """
    Initialize the LocalPygameClient with the given configuration and screen.
    """
    from tuxemon.client import LocalPygameClient

    try:
        client = LocalPygameClient(config, screen)
        logger.info("Client initialized successfully.")
    except (TypeError, ValueError) as e:
        logger.error(f"Failed to initialize client: {e}")
        raise
    except Exception as e:
        logger.critical(f"Unexpected error during client initialization: {e}")
        raise

    return client


def configure_game_states(
    client: LocalPygameClient,
    config: TuxemonConfig,
    load_slot: Optional[int] = None,
) -> None:
    # background state is used to prevent other states from
    # being required to track dirty screen areas.  for example,
    # in the start state, there is a menu on a blank background,
    # since menus do not clean up dirty areas, the blank,
    # "Background state" will do that.  The alternative is creating
    # a system for states to clean up their dirty screen areas.
    client.push_state("BackgroundState")
    if not config.skip_titlescreen:
        client.push_state("StartState")

    if load_slot:
        client.push_state("LoadMenuState", load_slot=load_slot)
        client.pop_state()

    elif config.splash:
        client.push_state("SplashState", parent=client.state_manager)
        client.push_state("FadeInTransition")

    if config.skip_titlescreen and config.mods and len(config.mods) == 1:
        destination = f"{prepare.STARTING_MAP}{config.mods[0]}.tmx"
        map_name = prepare.fetch("maps", destination)
        client.push_state("WorldState", map_name=map_name)


def configure_debug_options(client: LocalPygameClient) -> None:
    logger.info("********* DEBUG OPTIONS ENABLED *********")
    logging.basicConfig(level=logging.DEBUG)

    action = client.event_engine.execute_action
    action("add_monster", ("bigfin", 10))
    action("add_monster", ("dandylion", 10))
    action("add_item", ("potion",))
    action("add_item", ("cherry",))
    action("add_item", ("tuxeball",))
    for _ in range(10):
        action("add_item", ("super_potion",))
    for _ in range(100):
        action("add_item", ("apple",))


@no_type_check  # FIXME: dead code
def headless() -> None:
    """Sets up out headless server and start the game."""
    from tuxemon.client import HeadlessClient

    control = HeadlessClient()
    control.auto_state_discovery()
    control.push_state("HeadlessServerState")
    control.main()
