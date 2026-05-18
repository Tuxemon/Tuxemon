# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import pytest

from tuxemon.animation import (
    AnimationState,
    RetryTask,
    ScheduleType,
    TaskBase,
)


class DummyTask(TaskBase):
    _valid_schedules = (
        ScheduleType.ON_UPDATE,
        ScheduleType.ON_FINISH,
        ScheduleType.ON_ABORT,
    )

    def __init__(self):
        super().__init__()
        self.updated = 0
        self.finished = False
        self.aborted = False

    def update(self, dt):
        self.updated += 1
        if self.updated >= 2:
            self.finish()

    def finish(self):
        self._state = AnimationState.FINISHED
        self.finished = True
        self._execute_callbacks(ScheduleType.ON_FINISH)

    def abort(self):
        self._state = AnimationState.ABORTED
        self.aborted = True
        self._execute_callbacks(ScheduleType.ON_ABORT)


class AlwaysAbortTask(DummyTask):
    def update(self, dt):
        self.abort()


class AlwaysFinishTask(DummyTask):
    def update(self, dt):
        self.finish()


def test_retry_success_on_first_attempt():
    t = AlwaysFinishTask()
    retry = RetryTask(t, max_attempts=3)
    retry.start()
    retry.update(1)
    assert retry._state == AnimationState.FINISHED
    assert retry._current_attempt == 1


def test_retry_retries_on_abort():
    t = AlwaysAbortTask()
    retry = RetryTask(t, max_attempts=3)
    retry.start()
    retry.update(1)  # attempt 1 aborts → attempt 2
    retry.update(1)  # attempt 2 aborts → attempt 3
    retry.update(1)  # attempt 3 aborts → RetryTask aborts
    assert retry._state == AnimationState.ABORTED
    assert retry._current_attempt == 3


def test_retry_finishes_if_any_attempt_succeeds():
    class AbortThenFinish(TaskBase):
        _valid_schedules = (
            ScheduleType.ON_UPDATE,
            ScheduleType.ON_FINISH,
            ScheduleType.ON_ABORT,
        )

        def __init__(self):
            super().__init__()
            self.calls = 0

        def update(self, dt):
            self.calls += 1
            if self.calls == 1:
                self.abort()
            else:
                self.finish()

        def finish(self):
            self._state = AnimationState.FINISHED
            self._execute_callbacks(ScheduleType.ON_FINISH)

        def abort(self):
            self._state = AnimationState.ABORTED
            self._execute_callbacks(ScheduleType.ON_ABORT)

    retry = RetryTask(AbortThenFinish(), max_attempts=5)
    retry.start()
    retry.update(1)  # abort → retry
    retry.update(1)  # finish → success
    assert retry._state == AnimationState.FINISHED
    assert retry._current_attempt == 2


def test_retry_executes_update_callbacks():
    t = DummyTask()
    retry = RetryTask(t, max_attempts=2)
    called = []
    retry.schedule(lambda: called.append("update"), ScheduleType.ON_UPDATE)
    retry.start()
    retry.update(1)
    assert "update" in called


def test_retry_executes_finish_callbacks():
    t = AlwaysFinishTask()
    retry = RetryTask(t, max_attempts=2)
    called = []
    retry.schedule(lambda: called.append("finish"), ScheduleType.ON_FINISH)
    retry.start()
    retry.update(1)
    assert "finish" in called


def test_retry_executes_abort_callbacks():
    t = AlwaysAbortTask()
    retry = RetryTask(t, max_attempts=1)
    called = []
    retry.schedule(lambda: called.append("abort"), ScheduleType.ON_ABORT)
    retry.start()
    retry.update(1)
    assert "abort" in called


def test_retry_kill_clears_active_task():
    t = DummyTask()
    retry = RetryTask(t, max_attempts=2)
    retry.start()
    retry.kill()
    assert retry._active_task is None


def test_retry_invalid_attempts_raises():
    with pytest.raises(ValueError):
        RetryTask(DummyTask(), max_attempts=0)


def test_retry_update_before_start_does_nothing():
    t = DummyTask()
    retry = RetryTask(t, max_attempts=2)
    retry.update(1)
    assert retry._state == AnimationState.NOT_STARTED
    assert retry._current_attempt == 0


@pytest.mark.parametrize(
    "attempts",
    [
        pytest.param(1, id="one_attempt"),
        pytest.param(2, id="two_attempts"),
        pytest.param(5, id="five_attempts"),
    ],
)
def test_retry_parametrized_attempt_counts(attempts):
    t = AlwaysAbortTask()
    retry = RetryTask(t, max_attempts=attempts)

    retry.start()
    for _ in range(attempts):
        retry.update(1)

    assert retry._current_attempt == attempts
    assert retry._state == AnimationState.ABORTED
