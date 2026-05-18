# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import pytest

from tuxemon.step_tracker import (
    StepTracker,
    StepTrackerManager,
    decode_steps,
    encode_steps,
)


@pytest.fixture
def tracker():
    return StepTracker()


def test_initial_state(tracker):
    assert tracker.steps == 0.0
    assert tracker.countdown == 100.0
    assert tracker.milestones == [500, 250, 100, 50]


def test_step_update(tracker):
    tracker.update_steps(10, 5)
    assert tracker.steps == 15.0
    assert tracker.countdown == 85.0


def test_milestone_trigger(tracker):
    tracker.countdown = 49
    tracker.check_milestone_events()
    assert tracker.has_triggered_milestone(50)


def test_milestone_dialogue_shown(tracker):
    tracker.trigger_milestone_event(100)
    tracker.show_milestone_dialogue(100)
    assert tracker.has_shown_milestone(100)


def test_milestone_reached(tracker):
    tracker.update_steps(100, 0)
    assert tracker.has_reached_milestone(100)


def test_step_update_individual(tracker):
    tracker.update_steps(10, 5)
    assert tracker.steps == 15.0
    assert tracker.countdown == 85.0


def test_milestone_trigger_individual(tracker):
    tracker.countdown = 99
    tracker.check_milestone_events()
    tracker.trigger_milestone_event(100)
    assert tracker.has_triggered_milestone(100)


def test_auto_reset_with_overflow(tracker):
    tracker.auto_reset = True
    tracker.countdown = 10
    tracker.update_steps(15, 0)
    assert tracker.countdown == 95.0
    assert tracker.cycle_count == 1


def test_no_auto_reset(tracker):
    tracker.auto_reset = False
    tracker.countdown = 10
    tracker.update_steps(15, 0)
    assert tracker.countdown == 0
    assert tracker.cycle_count == 0


def test_milestone_status_reset_on_cycle(tracker):
    tracker.countdown = 49
    tracker.check_milestone_events()
    assert tracker.has_triggered_milestone(50)
    tracker.reset_cycle()
    assert not tracker.has_triggered_milestone(50)


def test_update_when_countdown_zero(tracker):
    tracker.auto_reset = True
    tracker.countdown = 0
    tracker.update_steps(5, 5)
    assert tracker.steps == 10.0
    assert tracker.countdown == 90.0
    assert tracker.cycle_count == 1


def test_multiple_milestones_triggered(tracker):
    tracker.auto_reset = False
    tracker.countdown = 260
    tracker.update_steps(150, 100)
    for m in [250, 100, 50]:
        assert tracker.has_triggered_milestone(m)


def test_serialization_cycle_count(tracker):
    tracker.cycle_count = 3
    tracker.auto_reset = False
    tracker.initial_countdown = 150

    manager = StepTrackerManager()
    manager.add_tracker("test", tracker)

    encoded = encode_steps(manager)
    decoded = decode_steps(encoded)
    decoded_tracker = decoded.get_tracker("test")

    assert decoded_tracker.cycle_count == 3
    assert decoded_tracker.auto_reset is False
    assert decoded_tracker.initial_countdown == 150


def test_decode_legacy_savegame_defaults():
    legacy_data = {
        "test": {
            "steps": 10.0,
            "countdown": 80.0,
            "milestones": [100, 50],
            "milestone_status": {"50": {"triggered": True, "shown": False}},
        }
    }
    decoded = decode_steps(legacy_data)
    tracker = decoded.get_tracker("test")

    assert tracker.initial_countdown == 80.0
    assert tracker.auto_reset is False
    assert tracker.cycle_count == 0


def test_invalid_milestone_access(tracker):
    assert tracker.has_triggered_milestone(999) is False
    assert tracker.has_shown_milestone(999) is False


def test_movement_equals_countdown(tracker):
    tracker.auto_reset = True
    tracker.countdown = 20
    tracker.update_steps(10, 10)
    assert tracker.countdown == 100.0
    assert tracker.cycle_count == 1


def test_multiple_resets_in_one_update(tracker):
    tracker.auto_reset = True
    tracker.countdown = 10
    tracker.update_steps(300, 0)
    assert tracker.cycle_count >= 2


def test_negative_movement(tracker):
    tracker.update_steps(-10, -5)
    assert tracker.countdown == 115.0


def test_empty_milestones(tracker):
    tracker.milestones = []
    tracker.countdown = 10
    tracker.update_steps(5, 5)
    assert tracker.milestone_status == {}


def test_triggered_not_shown(tracker):
    tracker.countdown = 49
    tracker.check_milestone_events()
    assert tracker.has_triggered_milestone(50)
    assert tracker.has_shown_milestone(50) is False


@pytest.fixture
def manager():
    m = StepTrackerManager()
    t1 = StepTracker()
    t2 = StepTracker()
    m.add_tracker("user1", t1)
    m.add_tracker("user2", t2)
    return m


def test_add_tracker(manager):
    assert "user1" in manager.trackers


def test_remove_tracker(manager):
    manager.remove_tracker("user1")
    assert "user1" not in manager.trackers


def test_update_all(manager):
    manager.update_all(20, 10)
    assert manager.get_tracker("user1").steps == 30.0


def test_encode_decode_steps(manager):
    encoded = encode_steps(manager)
    decoded = decode_steps(encoded)
    assert (
        decoded.get_tracker("user1").steps
        == manager.get_tracker("user1").steps
    )


def test_update_all_steps(manager):
    manager.update_all(20, 10)
    assert manager.get_tracker("user1").steps == 30.0
    assert manager.get_tracker("user2").steps == 30.0


def test_update_all_countdown(manager):
    manager.update_all(50, 20)
    assert manager.get_tracker("user1").countdown == 30.0
    assert manager.get_tracker("user2").countdown == 30.0


def test_milestone_not_triggered_globally(manager):
    tracker = manager.get_tracker("user1")
    milestone = tracker.milestones[-1]

    manager.update_all(10, 10)

    assert not manager.get_tracker("user1").has_triggered_milestone(milestone)
    assert not manager.get_tracker("user2").has_triggered_milestone(milestone)


def test_add_duplicate_tracker(manager, caplog):
    with caplog.at_level("ERROR"):
        manager.add_tracker("user1", StepTracker())
        assert "already exists" in caplog.text


def test_remove_nonexistent_tracker(manager, caplog):
    with caplog.at_level("ERROR"):
        manager.remove_tracker("ghost")
        assert "does not exist" in caplog.text


def test_get_nonexistent_tracker(manager):
    assert manager.get_tracker("ghost") is None
