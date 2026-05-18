# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock

import pytest

from tuxemon.db import Direction, FacingMode
from tuxemon.entity.path.commands import (
    ContinueCommand,
    PushCommand,
    RepathCommand,
    SpeedCommand,
    StopMovementCommand,
)
from tuxemon.entity.path.controller import PathController
from tuxemon.math import Vector2


class DummyNPC:
    def __init__(self):
        self.slug = "npc"
        self.tile_pos = (0, 0)
        self.position = Vector2(0, 0)
        self.facing = Direction.DOWN
        self.moving = False
        self.move_direction = None
        self.ignore_collisions = False
        self.mover = MoverCompat(self)
        self._moverate_modifier = 1.0

    def set_position(self, pos):
        self.position = Vector2(float(pos[0]), float(pos[1]))
        self.tile_pos = (int(pos[0]), int(pos[1]))

    def set_move_direction(self, d=None):
        self.move_direction = d
        if self.mover:
            self.mover.move_direction = d

    def stop_moving(self):
        self.moving = False

    def set_moverate_modifier(self, m):
        self._moverate_modifier = m
        if self.mover:
            self.mover.set_moverate_modifier(m)

    def on_tile_changed(self):
        pass

    def remove_collision(self):
        pass

    def begin_tile_exit(self):
        self.remove_collision()

    def complete_tile_entry(self, tile_pos):
        self.set_position(tile_pos)
        self.on_tile_changed()


class MoverCompat:
    """Compatibility wrapper for test doubles to mimic Mover interface."""

    def __init__(self, owner):
        self._owner = owner
        self.moverate_modifier = 1.0
        self.move_direction = None
        self.facing = Direction.DOWN
        self.facing_mode = FacingMode.FOLLOW_MOVEMENT
        self.base_moverate = 0.0
        self.move = None

    def set_moverate_modifier(self, modifier):
        self.moverate_modifier = max(0.0, modifier)
        self._owner._moverate_modifier = self.moverate_modifier

    def set_move_direction(self, direction=None):
        self.move_direction = direction
        self._owner.move_direction = direction

    def set_facing(self, direction):
        self.facing = direction
        self._owner.facing = direction

    def set_facing_mode(self, facing_mode):
        self.facing_mode = facing_mode

    def set_moverate(self, moverate):
        self.base_moverate = moverate

    def has_reached_next_tile(self, origin, target):
        return True


@pytest.fixture
def mk_controller():
    def _mk():
        npc = DummyNPC()
        npc.mover.move = MagicMock()
        sprite = MagicMock()
        sprite.play_animation = MagicMock()
        sprite.stop_animation = MagicMock()
        npc.sprite_controller = sprite
        pf = MagicMock()
        pf.is_tile_traversable.return_value = True
        pf.get_exits.return_value = []
        pf.pathfind.return_value = []
        mm = MagicMock()
        mm.collision_map.get.return_value = None
        nm = MagicMock()
        return PathController(npc, pf, mm, nm)

    return _mk


def test_execute_push_command(mk_controller):
    pc = mk_controller()
    pc.move_multiple_tiles = MagicMock()

    cmd = PushCommand(Direction.RIGHT, 3)
    pc.execute_command(cmd)

    pc.move_multiple_tiles.assert_called_once_with(Direction.RIGHT, 3)


def test_execute_speed_command(mk_controller):
    pc = mk_controller()
    npc = pc.owner

    cmd = SpeedCommand(0.5)
    pc.execute_command(cmd)

    assert npc._moverate_modifier == 0.5


def test_execute_continue_command(mk_controller):
    pc = mk_controller()
    pc.move_one_tile = MagicMock()

    cmd = ContinueCommand(Direction.UP)
    pc.execute_command(cmd)

    pc.move_one_tile.assert_called_once_with(Direction.UP)


def test_execute_repath_command_immediate(mk_controller):
    pc = mk_controller()
    pc.start_path = MagicMock()

    cmd = RepathCommand(destination=(5, 5), cooldown=0.5, immediate=True)
    pc.execute_command(cmd)

    assert pc._repath_cooldown == 0.5
    pc.start_path.assert_called_once_with((5, 5))


def test_execute_repath_command_delayed(mk_controller):
    pc = mk_controller()
    pc.start_path = MagicMock()

    cmd = RepathCommand(destination=(5, 5), cooldown=1.0, immediate=False)
    pc.execute_command(cmd)

    assert pc._repath_cooldown == 1.0
    pc.start_path.assert_not_called()


def test_execute_stop_command(mk_controller):
    pc = mk_controller()
    npc = pc.owner

    npc.stop_moving = MagicMock()
    cmd = StopMovementCommand()
    pc.execute_command(cmd)

    npc.stop_moving.assert_called_once()


def test_tile_effect_push_generates_command(mk_controller):
    pc = mk_controller()
    pc.move_multiple_tiles = MagicMock()

    tile = MagicMock()
    tile.push_effect.direction = Direction.LEFT
    tile.push_effect.strength = 2
    tile.speed_modifier = None
    tile.endure = None

    commands = pc.tile_effects.get_effects(tile, pc.owner, pc.path)
    assert len(commands) == 1
    assert isinstance(commands[0], PushCommand)

    for cmd in commands:
        pc.execute_command(cmd)

    pc.move_multiple_tiles.assert_called_once_with(Direction.LEFT, 2)


def test_tile_effect_speed_generates_command(mk_controller):
    pc = mk_controller()
    tile = MagicMock()
    tile.push_effect = None
    tile.speed_modifier = 0.25
    tile.endure = None

    commands = pc.tile_effects.get_effects(tile, pc.owner, pc.path)
    assert isinstance(commands[0], SpeedCommand)

    pc.execute_command(commands[0])
    assert pc.owner._moverate_modifier == 0.25


def test_tile_effect_continue_generates_command(mk_controller):
    pc = mk_controller()
    pc.move_one_tile = MagicMock()

    tile = MagicMock()
    tile.push_effect = None
    tile.speed_modifier = None
    tile.endure = [Direction.UP]

    commands = pc.tile_effects.get_effects(tile, pc.owner, pc.path)
    assert isinstance(commands[0], ContinueCommand)

    pc.execute_command(commands[0])
    pc.move_one_tile.assert_called_once_with(Direction.UP)


def test_reroute_policy_immediate_repath(mk_controller):
    pc = mk_controller()
    npc = pc.owner
    npc_manager = MagicMock()
    npc_manager.get_entity_pos.return_value = MagicMock()  # blocking NPC

    pc.start_path = MagicMock()
    pc.pathfinding = (7, 7)

    commands = pc.reroute_policy.on_obstruction(
        npc, npc_manager, pc.pathfinding, (0, 0)
    )
    assert len(commands) == 1
    assert isinstance(commands[0], RepathCommand)
    assert commands[0].immediate is True

    for cmd in commands:
        pc.execute_command(cmd)

    pc.start_path.assert_called_once_with((7, 7))
    assert pc._repath_cooldown == 0.5


def test_reroute_policy_delayed_repath(mk_controller):
    pc = mk_controller()
    npc = pc.owner
    npc_manager = MagicMock()
    npc_manager.get_entity_pos.return_value = None  # wall

    pc.pathfinding = (3, 3)
    npc.stop_moving = MagicMock()

    commands = pc.reroute_policy.on_obstruction(
        npc, npc_manager, pc.pathfinding, (0, 0)
    )
    assert len(commands) == 2
    assert isinstance(commands[0], RepathCommand)
    assert commands[0].immediate is False
    assert isinstance(commands[1], StopMovementCommand)

    for cmd in commands:
        pc.execute_command(cmd)

    assert pc._repath_cooldown == 1.0
    npc.stop_moving.assert_called_once()
