# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from tuxemon import log, prepare
from tuxemon.client import LocalPygameClient
from tuxemon.headless_client import HeadlessClient
from tuxemon.session import local_session

if TYPE_CHECKING:

    from tuxemon.config import TuxemonConfig


logger = logging.getLogger(__name__)


def main(config: TuxemonConfig, load_slot: Optional[int] = None) -> None:
    """
    Configure and start the game.

    Add all available states to our scene manager and start the game
    using the pygame interface.

    Parameters:
        config: The Tuxemon configuration object containing game settings.
        load_slot: Number of the save slot to load, if any.
    """
    log.configure()
    prepare.init()
    screen = prepare.SCREEN

    import pygame

    client = LocalPygameClient.create(config, screen)

    # global/singleton hack for now
    setattr(prepare, "GLOBAL_CONTROL", client)
    # WIP.  Will be more complete with game-view
    local_session.set_client(client)

    configure_game_states(client, config, load_slot)

    if config.collision_map:
        configure_debug_options(client)

    client.main()
    pygame.quit()


def configure_game_states(
    client: LocalPygameClient,
    config: TuxemonConfig,
    load_slot: Optional[int] = None,
) -> None:
    # The "BackgroundState" prevents other states from tracking dirty screen areas.
    # For example, menus in the start state don't clean up dirty areas, so a blank
    # background handles that instead of requiring each state to manage cleanup.
    client.push_state("BackgroundState")
    if not config.skip_titlescreen:
        client.push_state("StartState")

    if load_slot:
        client.push_state("LoadMenuState", load_slot=load_slot)
        client.pop_state()

    elif config.splash:
        client.push_state("SplashState", parent=client.state_manager)
        client.push_state("FadeInTransition")

    if config.skip_titlescreen and config.mods:
        if len(config.mods) == 1:
            destination = f"{prepare.STARTING_MAP}{config.mods[0]}.tmx"
            map_name = prepare.fetch("maps", destination)
            client.push_state(
                "WorldState", session=local_session, map_name=map_name
            )
        else:
            client.push_state("ModsChoice", mods=config.mods)


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


def headless(config: TuxemonConfig) -> None:
    """
    Sets up out headless server and start the game.

    Parameters:
        config: The Tuxemon configuration object containing game settings.
    """
    control = HeadlessClient(config)
    control.push_state("HeadlessServerState")
    control.main()
