# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import pytest

from tuxemon.animation import (
    AnimationState,
    RaceTask,
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


def test_race_starts_all_tasks():
    t1 = DummyTask()
    t2 = DummyTask()
    race = RaceTask(t1, t2)
    race.start()
    assert t1._state == AnimationState.RUNNING
    assert t2._state == AnimationState.RUNNING


def test_race_finishes_when_first_task_finishes():
    t1 = InstantFinishTask()
    t2 = DummyTask()
    race = RaceTask(t1, t2)
    race.start()
    race.update(1)
    assert race._state == AnimationState.FINISHED
    assert race._winner is t1
    assert t2.aborted


def test_race_aborts_when_first_task_aborts():
    t1 = InstantAbortTask()
    t2 = DummyTask()
    race = RaceTask(t1, t2)
    race.start()
    race.update(1)
    assert race._state == AnimationState.ABORTED
    assert race._winner is t1
    assert t2.aborted


def test_race_update_propagates_to_all_running_tasks():
    t1 = DummyTask()
    t2 = DummyTask()
    race = RaceTask(t1, t2)
    race.start()
    race.update(1)
    assert t1.updated == 1
    assert t2.updated == 1


def test_race_executes_update_callbacks():
    t1 = DummyTask()
    t2 = DummyTask()
    race = RaceTask(t1, t2)
    called = []
    race.schedule(lambda: called.append("update"), ScheduleType.ON_UPDATE)
    race.start()
    race.update(1)
    assert "update" in called


def test_race_executes_finish_callbacks():
    t1 = InstantFinishTask()
    t2 = DummyTask()
    race = RaceTask(t1, t2)
    called = []
    race.schedule(lambda: called.append("finish"), ScheduleType.ON_FINISH)
    race.start()
    race.update(1)
    assert "finish" in called


def test_race_executes_abort_callbacks():
    t1 = InstantAbortTask()
    t2 = DummyTask()
    race = RaceTask(t1, t2)
    called = []
    race.schedule(lambda: called.append("abort"), ScheduleType.ON_ABORT)
    race.start()
    race.update(1)
    assert "abort" in called


def test_race_kill_clears_tasks():
    t1 = DummyTask()
    t2 = DummyTask()
    race = RaceTask(t1, t2)
    race.start()
    race.kill()
    assert race._tasks == []


def test_race_update_before_start_does_nothing():
    t1 = DummyTask()
    t2 = DummyTask()
    race = RaceTask(t1, t2)
    race.update(1)
    assert t1.updated == 0
    assert t2.updated == 0
    assert race._state == AnimationState.NOT_STARTED


@pytest.mark.parametrize(
    "winner_type",
    [
        pytest.param(InstantFinishTask, id="instant_finish"),
        pytest.param(InstantAbortTask, id="instant_abort"),
    ],
)
def test_race_parametrized_winner_types(winner_type):
    winner = winner_type()
    loser = DummyTask()
    race = RaceTask(winner, loser)
    race.start()
    race.update(1)
    assert race._winner is winner
    assert loser.aborted


def test_race_multiple_tasks_finish_simultaneously():
    # Both finish on first update
    t1 = InstantFinishTask()
    t2 = InstantFinishTask()
    race = RaceTask(t1, t2)
    race.start()
    race.update(1)
    assert race._winner in (t1, t2)
    loser = t1 if race._winner is t2 else t2
    assert loser.aborted
