# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import pytest

from tuxemon.animation import (
    AnimationState,
    ConditionalTask,
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


class InstantTask(DummyTask):
    def update(self, dt):
        self.finish()


class AbortTask(DummyTask):
    def update(self, dt):
        self.abort()


def test_conditional_runs_true_branch():
    t_true = DummyTask()
    t_false = DummyTask()
    cond = ConditionalTask(lambda: True, t_true, t_false)

    cond.start()
    cond.update(1)

    assert t_true.updated == 1
    assert t_false.updated == 0


def test_conditional_runs_false_branch():
    t_true = DummyTask()
    t_false = DummyTask()
    cond = ConditionalTask(lambda: False, t_true, t_false)

    cond.start()
    cond.update(1)

    assert t_false.updated == 1
    assert t_true.updated == 0


@pytest.mark.parametrize(
    "predicate",
    [
        pytest.param(True, id="predicate_true"),
        pytest.param(False, id="predicate_false"),
    ],
)
def test_conditional_starts_only_selected_task(predicate):
    t_true = DummyTask()
    t_false = DummyTask()
    cond = ConditionalTask(lambda: predicate, t_true, t_false)

    cond.start()

    if predicate:
        assert cond._active_task is t_true
        assert t_false.updated == 0
    else:
        assert cond._active_task is t_false
        assert t_true.updated == 0


def test_conditional_finishes_when_child_finishes():
    t_true = DummyTask()
    cond = ConditionalTask(lambda: True, t_true, DummyTask())

    cond.start()
    cond.update(1)
    cond.update(1)

    assert t_true.finished
    assert cond._state == AnimationState.FINISHED


def test_conditional_finishes_when_child_aborts():
    t_true = AbortTask()
    cond = ConditionalTask(lambda: True, t_true, DummyTask())

    cond.start()
    cond.update(1)

    assert t_true.aborted
    assert cond._state == AnimationState.FINISHED


def test_conditional_abort_propagates_to_child():
    t_true = DummyTask()
    cond = ConditionalTask(lambda: True, t_true, DummyTask())

    cond.start()
    cond.abort()

    assert t_true.aborted
    assert cond._state == AnimationState.ABORTED


def test_conditional_executes_callbacks():
    t_true = DummyTask()
    cond = ConditionalTask(lambda: True, t_true, DummyTask())

    called = []
    cond.schedule(lambda: called.append("update"), ScheduleType.ON_UPDATE)
    cond.schedule(lambda: called.append("finish"), ScheduleType.ON_FINISH)

    cond.start()
    cond.update(1)
    cond.update(1)

    assert "update" in called
    assert "finish" in called


def test_conditional_handles_instant_tasks():
    t_true = InstantTask()
    cond = ConditionalTask(lambda: True, t_true, DummyTask())

    cond.start()
    cond.update(1)

    assert t_true.finished
    assert cond._state == AnimationState.FINISHED


def test_conditional_child_abort_advances():
    t_true = AbortTask()
    cond = ConditionalTask(lambda: True, t_true, DummyTask())

    cond.start()
    cond.update(1)

    assert t_true.aborted
    assert cond._state == AnimationState.FINISHED


def test_conditional_update_before_start_does_nothing():
    t_true = DummyTask()
    cond = ConditionalTask(lambda: True, t_true, DummyTask())

    cond.update(1)
    assert t_true.updated == 0
    assert cond._state == AnimationState.NOT_STARTED


def test_conditional_kill_clears_active_task():
    t_true = DummyTask()
    cond = ConditionalTask(lambda: True, t_true, DummyTask())

    cond.start()
    cond.kill()

    assert cond._active_task is None
