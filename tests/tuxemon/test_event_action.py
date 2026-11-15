# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock

import pytest

from tuxemon.event.eventaction import ActionContextManager
from tuxemon.session import Session


@pytest.fixture
def mock_action():
    action = MagicMock()
    action.cancelled = False
    return action


@pytest.fixture
def mock_session():
    return MagicMock(spec=Session)


class TestActionContextManager:
    def test_enter_calls_on_start(self, mock_action, mock_session):
        with ActionContextManager(mock_action, mock_session):
            mock_action.on_start.assert_called_once_with(mock_session)

    def test_exit_calls_cleanup(self, mock_action, mock_session):
        with ActionContextManager(mock_action, mock_session):
            pass
        mock_action.cleanup.assert_called_once_with(mock_session)

    def test_cancelled_action_skips_on_start(self, mock_action, mock_session):
        mock_action.cancelled = True
        with ActionContextManager(mock_action, mock_session):
            mock_action.on_start.assert_not_called()
        mock_action.cleanup.assert_called_once_with(mock_session)

    def test_cleanup_always_called_even_when_cancelled(
        self, mock_action, mock_session
    ):
        mock_action.cancelled = True
        with ActionContextManager(mock_action, mock_session):
            pass
        assert mock_action.cleanup.call_count == 1

    def test_cleanup_called_on_exception(self, mock_action, mock_session):
        with pytest.raises(ValueError):
            with ActionContextManager(mock_action, mock_session):
                raise ValueError("body error")
        mock_action.cleanup.assert_called_once_with(mock_session)

    def test_cleanup_exception_propagates(self, mock_action, mock_session):
        mock_action.cleanup.side_effect = RuntimeError("cleanup error")
        with pytest.raises(RuntimeError, match="cleanup error"):
            with ActionContextManager(mock_action, mock_session):
                pass

    def test_body_exception_not_swallowed_when_cleanup_is_clean(
        self, mock_action, mock_session
    ):
        with pytest.raises(ValueError, match="body error"):
            with ActionContextManager(mock_action, mock_session):
                raise ValueError("body error")

    def test_enter_returns_action(self, mock_action, mock_session):
        with ActionContextManager(mock_action, mock_session) as action:
            assert action is mock_action
