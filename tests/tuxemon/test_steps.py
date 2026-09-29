# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock

from tuxemon.monster.listener import monster_update_listener


def make_monster(steps=0, waiting_to_evolve=False, evolutions=None):
    monster = MagicMock()
    monster.steps = steps
    monster.waiting_to_evolve = waiting_to_evolve
    monster.evolutions = evolutions or []
    monster.status = None
    return monster


def test_listener_increments_steps():
    monster = make_monster(steps=0)
    monster_update_listener(steps=5.0, monsters=[monster], session=MagicMock())
    assert monster.steps == 5.0


def test_listener_flags_waiting_to_evolve():
    evo = MagicMock()
    evo.steps = 10
    monster = make_monster(steps=9, evolutions=[evo])
    monster_update_listener(steps=1.0, monsters=[monster], session=MagicMock())
    assert monster.waiting_to_evolve is True


def test_listener_does_not_flag_if_steps_not_met():
    evo = MagicMock()
    evo.steps = 10
    monster = make_monster(steps=0, evolutions=[evo])
    monster_update_listener(steps=1.0, monsters=[monster], session=MagicMock())
    assert monster.waiting_to_evolve is False


def test_listener_skips_check_if_already_waiting():
    evo = MagicMock()
    evo.steps = 10
    monster = make_monster(steps=10, waiting_to_evolve=True, evolutions=[evo])
    monster_update_listener(steps=1.0, monsters=[monster], session=MagicMock())
    # waiting_to_evolve was already True, no change expected
    assert monster.waiting_to_evolve is True


def test_listener_skips_evolution_with_no_steps_condition():
    evo = MagicMock()
    evo.steps = None
    monster = make_monster(steps=100, evolutions=[evo])
    monster_update_listener(steps=1.0, monsters=[monster], session=MagicMock())
    assert monster.waiting_to_evolve is False
