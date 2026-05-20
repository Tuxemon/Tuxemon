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
    # NPC blocks the *target* tile
    def get_entity_at_pos(pos):
        if pos == (6, 5):
            return MagicMock()
        return None

    npc_manager.get_entity_pos.side_effect = get_entity_at_pos

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


def test_reroute_policy_prioritizes_npc_over_wall_obstruction(
    npc, npc_manager
):
    # If an NPC is present, it must ALWAYS trigger immediate repath
    npc_manager.get_entity_pos.return_value = MagicMock()

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
    assert cmd.immediate is True
    assert cmd.cooldown == 0.5


def test_ghost_policy_waits_if_destination_blocked(npc, npc_manager):
    # Destination tile blocked, target tile clear
    def get_entity_at_pos(pos):
        if pos == (10, 10):
            return MagicMock()
        return None

    npc_manager.get_entity_pos.side_effect = get_entity_at_pos

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
    npc_manager.get_entity_pos.return_value = None  # No NPC blocking anything

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


def test_ghost_policy_ignores_midway_npc_if_destination_clear(
    npc, npc_manager
):
    # NPC blocks the *target* tile, but destination is clear
    def get_entity_at_pos(pos):
        if pos == (6, 5):
            return MagicMock()
        return None

    npc_manager.get_entity_pos.side_effect = get_entity_at_pos

    policy = GhostReroutePolicy()
    commands = policy.on_obstruction(
        owner=npc,
        npc_manager=npc_manager,
        pathfinding=(10, 10),
        target=(6, 5),
    )

    # Ghost should phase through anyway
    assert len(commands) == 1
    assert isinstance(commands[0], ContinueCommand)


def test_ghost_policy_zero_distance_movement(npc, npc_manager):
    npc_manager.get_entity_pos.return_value = None

    policy = GhostReroutePolicy()
    commands = policy.on_obstruction(
        owner=npc,
        npc_manager=npc_manager,
        pathfinding=(10, 10),
        target=(5, 5),  # Same tile as NPC
    )

    assert len(commands) == 1
    assert isinstance(commands[0], ContinueCommand)
    # Direction may be NONE depending on implementation, but command must exist


def test_ghost_policy_no_pathfinding_phases_through(npc, npc_manager):
    npc_manager.get_entity_pos.return_value = None

    policy = GhostReroutePolicy()
    commands = policy.on_obstruction(
        owner=npc,
        npc_manager=npc_manager,
        pathfinding=None,
        target=(6, 5),
    )

    assert len(commands) == 1
    cmd = commands[0]
    assert isinstance(cmd, ContinueCommand)
    assert cmd.direction == Direction.RIGHT


def test_ghost_policy_ignores_any_target_obstruction_if_destination_clear(
    npc, npc_manager
):
    # Target tile blocked by something (NPC or treated as obstruction), destination clear
    def get_entity_at_pos(pos):
        if pos == (6, 5):  # target tile
            return MagicMock()  # obstruction at target
        return None  # destination (10,10) is clear

    npc_manager.get_entity_pos.side_effect = get_entity_at_pos

    policy = GhostReroutePolicy()
    commands = policy.on_obstruction(
        owner=npc,
        npc_manager=npc_manager,
        pathfinding=(10, 10),
        target=(6, 5),
    )

    assert len(commands) == 1
    assert isinstance(commands[0], ContinueCommand)
