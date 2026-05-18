# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock

import pytest

from tuxemon.db import Direction
from tuxemon.entity.path.commands import (
    ContinueCommand,
    RepathCommand,
    StopMovementCommand,
)
from tuxemon.entity.path.policies.reroute import (
    GhostReroutePolicy,
    ReroutePolicy,
)


class DummyNPC:
    def __init__(self):
        self.slug = "ghost"
        self.tile_pos = (5, 5)


@pytest.fixture
def npc():
    return DummyNPC()


@pytest.fixture
def npc_manager():
    return MagicMock()


def test_reroute_policy_immediate_repath_when_npc_blocking(npc, npc_manager):
    npc_manager.get_entity_pos.return_value = MagicMock()  # NPC blocking

    policy = ReroutePolicy()
    commands = policy.on_obstruction(
        owner=npc,
        npc_manager=npc_manager,
        pathfinding=(10, 10),
        target=(6, 5),
    )

    assert len(commands) == 1
    cmd = commands[0]
    assert isinstance(cmd, RepathCommand)
    assert cmd.destination == (10, 10)
    assert cmd.cooldown == 0.5
    assert cmd.immediate is True


def test_reroute_policy_delayed_repath_when_wall(npc, npc_manager):
    npc_manager.get_entity_pos.return_value = None  # No NPC blocking

    policy = ReroutePolicy()
    commands = policy.on_obstruction(
        owner=npc,
        npc_manager=npc_manager,
        pathfinding=(10, 10),
        target=(6, 5),
    )

    assert len(commands) == 2
    repath, stop = commands

    assert isinstance(repath, RepathCommand)
    assert repath.destination == (10, 10)
    assert repath.cooldown == 1.0
    assert repath.immediate is False

    assert isinstance(stop, StopMovementCommand)


def test_reroute_policy_simple_obstruction_no_pathfinding(npc, npc_manager):
    policy = ReroutePolicy()
    commands = policy.on_obstruction(
        owner=npc,
        npc_manager=npc_manager,
        pathfinding=None,
        target=(6, 5),
    )

    assert len(commands) == 1
    assert isinstance(commands[0], StopMovementCommand)


def test_ghost_policy_waits_if_destination_blocked(npc, npc_manager):
    npc_manager.get_entity_pos.return_value = MagicMock()  # NPC blocking

    policy = GhostReroutePolicy()
    commands = policy.on_obstruction(
        owner=npc,
        npc_manager=npc_manager,
        pathfinding=(10, 10),
        target=(6, 5),
    )

    assert len(commands) == 2
    repath, stop = commands

    assert isinstance(repath, RepathCommand)
    assert repath.destination == (10, 10)
    assert repath.cooldown == 2.0
    assert repath.immediate is False

    assert isinstance(stop, StopMovementCommand)


def test_ghost_policy_phases_through_walls(npc, npc_manager):
    npc_manager.get_entity_pos.return_value = None  # No NPC blocking

    policy = GhostReroutePolicy()
    commands = policy.on_obstruction(
        owner=npc,
        npc_manager=npc_manager,
        pathfinding=(10, 10),
        target=(6, 5),
    )

    assert len(commands) == 1
    cmd = commands[0]

    assert isinstance(cmd, ContinueCommand)
    assert cmd.direction == Direction.RIGHT  # (5,5) → (6,5)
