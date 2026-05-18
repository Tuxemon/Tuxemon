# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from tuxemon.client import LocalPygameClient
from tuxemon.headless_client import HeadlessClient
from tuxemon.session import local_session
from tuxemon.startup_state_machine import StartupStateMachine

if TYPE_CHECKING:
    from tuxemon.config import TuxemonConfig
    from tuxemon.prepare import DisplayContext

logger = logging.getLogger(__name__)


def main(
    config: TuxemonConfig,
    context: DisplayContext,
    load_slot: int | None = None,
) -> None:
    """
    Initialize and launch the game using a local Pygame client.

    Sets up logging, creates the game client, configures initial states,
    applies debug options when enabled, and starts the main game loop.
    """

    import pygame

    client = LocalPygameClient.create(config, context)
    local_session.set_client(client)

    configure_game_states(client, config, load_slot)

    if config.collision_map:
        configure_debug_options(client)

    client.main()
    pygame.quit()


def headless(config: TuxemonConfig, context: DisplayContext) -> None:
    """
    Start the game in headless mode for server or automated use.

    Configures logging, initializes the headless client, loads the
    headless server state, and runs the main loop without graphics.
    """
    control = HeadlessClient(config, context)
    control.push_state("HeadlessServerState")
    control.main()


def configure_game_states(
    client: LocalPygameClient,
    config: TuxemonConfig,
    load_slot: int | None = None,
) -> None:
    machine = StartupStateMachine(client, config, load_slot)
    machine.run()


def configure_debug_options(client: LocalPygameClient) -> None:
    logger.info("********* DEBUG OPTIONS ENABLED *********")

    logger.setLevel(logging.DEBUG)

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
