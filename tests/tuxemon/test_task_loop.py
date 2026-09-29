# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from copy import deepcopy

import pytest

from tuxemon.animation import (
    AnimationState,
    LoopTask,
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
        self._state = AnimationState.RUNNING

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


class InstantFinishTask(DummyTask):
    def update(self, dt):
        self.finish()


class InstantAbortTask(DummyTask):
    def update(self, dt):
        self.abort()


def test_loop_runs_task_multiple_times():
    t = DummyTask()
    loop = LoopTask(t, times=3)

    loop.start()
    for _ in range(10):
        loop.update(1)

    assert loop._state == AnimationState.FINISHED
    assert loop._current_loop == 3


def test_loop_clones_task_each_iteration():
    t = DummyTask()
    loop = LoopTask(t, times=2)
    loop.start()
    first_task = loop._active_task
    loop.update(1)
    loop.update(1)  # first iteration finishes → second begins
    second_task = loop._active_task
    assert first_task is not second_task
    assert deepcopy(t) != t  # sanity check: deepcopy works


def test_loop_continues_even_if_child_aborts():
    t = InstantAbortTask()
    loop = LoopTask(t, times=3)
    loop.start()
    loop.update(1)  # abort → next loop
    loop.update(1)  # abort → next loop
    loop.update(1)  # abort → finish
    assert loop._state == AnimationState.FINISHED
    assert loop._current_loop == 3


def test_loop_finishes_after_all_iterations():
    t = InstantFinishTask()
    loop = LoopTask(t, times=5)

    loop.start()
    for _ in range(5):
        loop.update(1)

    assert loop._state == AnimationState.FINISHED
    assert loop._current_loop == 5


def test_loop_executes_update_callbacks():
    t = DummyTask()
    loop = LoopTask(t, times=1)
    called = []
    loop.schedule(lambda: called.append("update"), ScheduleType.ON_UPDATE)
    loop.start()
    loop.update(1)
    assert "update" in called


def test_loop_executes_finish_callbacks():
    t = InstantFinishTask()
    loop = LoopTask(t, times=1)
    called = []
    loop.schedule(lambda: called.append("finish"), ScheduleType.ON_FINISH)
    loop.start()
    loop.update(1)
    assert "finish" in called


def test_loop_abort_aborts_active_task():
    t = DummyTask()
    loop = LoopTask(t, times=3)
    loop.start()
    loop.abort()
    assert loop._state == AnimationState.ABORTED
    assert loop._active_task is None or t.aborted


def test_loop_kill_clears_active_task():
    t = DummyTask()
    loop = LoopTask(t, times=2)
    loop.start()
    loop.kill()
    assert loop._active_task is None


def test_loop_invalid_times_raises():
    with pytest.raises(ValueError):
        LoopTask(DummyTask(), times=0)


def test_loop_update_before_start_does_nothing():
    t = DummyTask()
    loop = LoopTask(t, times=2)
    loop.update(1)
    assert loop._current_loop == 0
    assert loop._state == AnimationState.NOT_STARTED


@pytest.mark.parametrize(
    "times",
    [
        pytest.param(1, id="one_loop"),
        pytest.param(2, id="two_loops"),
        pytest.param(5, id="five_loops"),
    ],
)
def test_loop_parametrized(times):
    t = InstantFinishTask()
    loop = LoopTask(t, times=times)

    loop.start()
    for _ in range(times):
        loop.update(1)

    assert loop._state == AnimationState.FINISHED
    assert loop._current_loop == times
