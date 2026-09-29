# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import Mock

import pytest

from tuxemon.state.repository import StateRepository


@pytest.fixture
def repo():
    return StateRepository()


@pytest.fixture
def mock_state1():
    s = Mock()
    s.__name__ = "State1"
    return s


@pytest.fixture
def mock_state2():
    s = Mock()
    s.__name__ = "State2"
    return s


def test_add_state(repo, mock_state1):
    repo.add_state(mock_state1)
    assert "State1" in repo._state_dict
    assert repo._state_dict["State1"] is mock_state1


def test_add_duplicate_state_strict(repo, mock_state1):
    repo.add_state(mock_state1)
    with pytest.raises(ValueError):
        repo.add_state(mock_state1, True)


def test_add_duplicate_state_no_strict(repo, mock_state1):
    repo.add_state(mock_state1)
    # should not raise
    repo.add_state(mock_state1, False)


def test_get_state(repo, mock_state1):
    repo.add_state(mock_state1)
    assert repo.get_state("State1") is mock_state1


def test_get_nonexistent_state(repo):
    with pytest.raises(ValueError):
        repo.get_state("NonexistentState")


def test_all_states(repo, mock_state1, mock_state2):
    repo.add_state(mock_state1)
    repo.add_state(mock_state2)
    states = repo.all_states()

    assert len(states) == 2
    assert "State1" in states
    assert "State2" in states


def test_add_multiple_states(repo, mock_state1, mock_state2):
    repo.add_state(mock_state1)
    repo.add_state(mock_state2)

    assert "State1" in repo._state_dict
    assert "State2" in repo._state_dict
