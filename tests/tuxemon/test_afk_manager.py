# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import pytest

from tuxemon.event import get_event_bus
from tuxemon.platform.afk_manager import AFKManager


@pytest.fixture
def bus():
    bus = get_event_bus()
    bus._listeners.clear()
    return bus


@pytest.fixture
def manager(bus):
    return AFKManager()


@pytest.fixture
def event_collector(bus):
    """Collects emitted events for assertions."""
    events = []

    def make_listener(event_name):
        def _listener(**kwargs):
            events.append((event_name, kwargs))

        return _listener

    bus.subscribe(
        "afk.threshold_reached", make_listener("afk.threshold_reached")
    )
    bus.subscribe("afk.reset", make_listener("afk.reset"))

    return events


def test_add_threshold_valid(manager):
    manager.add_threshold("warn", 10.0)
    assert len(manager.thresholds) == 1
    assert manager.thresholds[0].level == "warn"


def test_add_threshold_invalid_duration(manager):
    manager.add_threshold("bad", -5.0)
    assert len(manager.thresholds) == 0


def test_add_threshold_duplicate(manager):
    manager.add_threshold("warn", 5.0)
    manager.add_threshold("warn", 10.0)
    assert len(manager.thresholds) == 1
    assert manager.get_duration_by_level("warn") == 5.0


def test_remove_threshold(manager):
    manager.add_threshold("warn", 10.0)
    assert manager.remove_threshold("warn")
    assert len(manager.thresholds) == 0


def test_remove_threshold_nonexistent(manager):
    assert not manager.remove_threshold("missing")


def test_modify_threshold(manager):
    manager.add_threshold("warn", 10.0)
    assert manager.modify_threshold("warn", 20.0)
    assert manager.thresholds[0].duration == 20.0


def test_modify_threshold_nonexistent(manager):
    assert not manager.modify_threshold("missing", 20.0)


def test_update_triggers_threshold(manager, event_collector):
    manager.add_threshold("warn", 5.0)
    result = manager.update(6.0)

    assert result == "warn"
    assert "warn" in manager.active_levels
    assert event_collector[0][0] == "afk.threshold_reached"


def test_update_no_change(manager, event_collector):
    manager.add_threshold("warn", 5.0)
    manager.update(2.0)

    assert len(event_collector) == 0
    assert manager.current_level is None


def test_update_negative_time_delta(manager):
    manager.add_threshold("warn", 5.0)
    manager.update(-3.0)
    assert manager.current_idle_time == 0.0


def test_update_triggers_highest_threshold(manager):
    manager.add_threshold("warn", 5.0)
    manager.add_threshold("kick", 10.0)

    result = manager.update(12.0)

    assert result == "kick"
    assert "warn" in manager.active_levels
    assert "kick" in manager.active_levels


def test_multiple_thresholds(manager):
    manager.add_threshold("warn", 5.0)
    manager.add_threshold("kick", 10.0)

    manager.update(6.0)
    assert "warn" in manager.active_levels
    assert "kick" not in manager.active_levels

    manager.update(5.0)
    assert "kick" in manager.active_levels


def test_reset_clears_state(manager, event_collector):
    manager.add_threshold("warn", 5.0)
    manager.update(6.0)

    old_level = manager.reset()

    assert old_level == "warn"
    assert len(manager.active_levels) == 0
    assert event_collector[-1][0] == "afk.reset"


def test_reset_when_not_afk(manager):
    old_level = manager.reset()
    assert old_level is None
    assert manager.current_idle_time == 0.0


def test_current_level_property(manager):
    manager.add_threshold("warn", 5.0)
    manager.add_threshold("kick", 10.0)
    manager.update(11.0)

    assert manager.current_level == "kick"


def test_is_threshold_met(manager):
    manager.add_threshold("warn", 5.0)
    manager.update(6.0)

    assert manager.is_threshold_met("warn")
    assert not manager.is_threshold_met("kick")


def test_get_duration_by_level(manager):
    manager.add_threshold("warn", 5.0)

    assert manager.get_duration_by_level("warn") == 5.0
    assert manager.get_duration_by_level("missing") == 0.0


def test_modify_threshold_resets_state(manager):
    manager.add_threshold("warn", 5.0)
    manager.update(6.0)

    assert "warn" in manager.active_levels

    manager.modify_threshold("warn", 20.0)

    assert len(manager.active_levels) == 0
    assert manager._next_threshold_index == 0


def test_threshold_map_consistency(manager):
    manager.add_threshold("warn", 5.0)
    assert manager.threshold_map["warn"] == 5.0

    manager.modify_threshold("warn", 15.0)
    assert manager.threshold_map["warn"] == 15.0

    manager.remove_threshold("warn")
    assert "warn" not in manager.threshold_map


def test_stress_game_loop_updates(manager):
    manager.add_threshold("warn", 5.0)
    manager.add_threshold("kick", 10.0)
    manager.add_threshold("ban", 20.0)

    for second in range(25):
        result = manager.update(1.0)

        if second + 1 == 5:
            assert result == "warn"
        elif second + 1 == 10:
            assert result == "kick"
        elif second + 1 == 20:
            assert result == "ban"
        else:
            assert result is None

    assert "warn" in manager.active_levels
    assert "kick" in manager.active_levels
    assert "ban" in manager.active_levels
    assert manager.current_level == "ban"
