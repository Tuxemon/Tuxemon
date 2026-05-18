# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import ANY, Mock

import pytest

from tuxemon.db import SeenStatus
from tuxemon.tuxepedia.data import TuxepediaData
from tuxemon.tuxepedia.manager import (
    EVENT_MONSTER_ADDED,
    EVENT_MONSTER_REMOVED,
    EVENT_MONSTER_STATUS_UPDATED,
    EVENT_TUXEPEDIA_RESET,
    MonsterEntry,
    TuxepediaManager,
    decode_tuxepedia,
    encode_tuxepedia,
)
from tuxemon.tuxepedia.reporter import TuxepediaReporter


# TestMonsterEntry
@pytest.mark.parametrize(
    "initial_status,initial_appearance,update_to,expected_status,expected_appearance,expected_caught",
    [
        pytest.param(
            SeenStatus.SEEN, 1, None, SeenStatus.SEEN, 1, 0, id="defaults"
        ),
        pytest.param(
            SeenStatus.SEEN,
            1,
            SeenStatus.CAUGHT,
            SeenStatus.CAUGHT,
            2,
            1,
            id="caught",
        ),
        pytest.param(
            SeenStatus.CAUGHT,
            1,
            SeenStatus.SEEN,
            SeenStatus.CAUGHT,
            1,
            0,
            id="no_downgrade",
        ),
        pytest.param(
            SeenStatus.CAUGHT, 5, "reset", SeenStatus.SEEN, 1, 0, id="reset"
        ),
    ],
)
def test_monster_entry_behaviors(
    initial_status,
    initial_appearance,
    update_to,
    expected_status,
    expected_appearance,
    expected_caught,
):
    entry = MonsterEntry(
        status=initial_status, appearance_count=initial_appearance
    )
    if update_to == "reset":
        entry.reset_entry()
    elif update_to:
        entry.update_status(update_to)
    assert entry.status == expected_status
    assert entry.appearance_count == expected_appearance
    assert entry.caught_count == expected_caught


# TestTuxepediaData
@pytest.fixture
def data():
    initial_entries = {
        "rockitten": MonsterEntry(SeenStatus.SEEN, 2),
        "nut": MonsterEntry(SeenStatus.CAUGHT, 5),
        "flowey": MonsterEntry(SeenStatus.SEEN, 1),
    }
    return TuxepediaData(initial_entries)


def test_init():
    empty_data = TuxepediaData()
    assert empty_data.entries == {}


@pytest.mark.parametrize(
    "slug,expected_status,expected_appearance,expected_caught,is_registered",
    [
        pytest.param("nut", SeenStatus.CAUGHT, 5, 0, True, id="nut"),
        pytest.param("rockitten", SeenStatus.SEEN, 2, 0, True, id="rockitten"),
        pytest.param("flowey", SeenStatus.SEEN, 1, 0, True, id="flowey"),
        pytest.param("unknown", None, 0, 0, False, id="unknown"),
    ],
)
def test_data_accessors(
    data,
    slug,
    expected_status,
    expected_appearance,
    expected_caught,
    is_registered,
):
    assert data.get_status(slug) == expected_status
    assert data.get_appearance(slug) == expected_appearance
    assert data.get_caught(slug) == expected_caught
    assert data.is_registered(slug) == is_registered


# TestTuxepediaManager
class MockEventBus:
    def __init__(self):
        self.publish = Mock()


@pytest.fixture
def event_bus():
    return MockEventBus()


@pytest.fixture
def manager(event_bus):
    return TuxepediaManager(event_bus)


@pytest.mark.parametrize(
    "slug,status,expected_event,expected_status,expected_appearance,expected_caught,expect_error",
    [
        pytest.param(
            "rockitten",
            SeenStatus.SEEN,
            EVENT_MONSTER_ADDED,
            SeenStatus.SEEN,
            1,
            0,
            None,
            id="add_seen",
        ),
        pytest.param(
            "rockitten",
            SeenStatus.CAUGHT,
            EVENT_MONSTER_STATUS_UPDATED,
            SeenStatus.CAUGHT,
            2,
            1,
            None,
            id="update_caught",
        ),
        pytest.param(
            "nut",
            SeenStatus.CAUGHT,
            EVENT_MONSTER_REMOVED,
            SeenStatus.CAUGHT,
            1,
            0,
            None,
            id="remove_entry",
        ),
        pytest.param(
            "ghost",
            SeenStatus.SEEN,
            EVENT_MONSTER_REMOVED,
            SeenStatus.SEEN,
            0,
            0,
            ValueError,
            id="remove_nonexistent",
        ),
    ],
)
def test_add_update_remove(
    manager,
    event_bus,
    slug,
    status,
    expected_event,
    expected_status,
    expected_appearance,
    expected_caught,
    expect_error,
):
    if expected_event == EVENT_MONSTER_STATUS_UPDATED:
        manager.register_seen(slug)
    elif expected_event == EVENT_MONSTER_REMOVED and expect_error is None:
        if status == SeenStatus.CAUGHT:
            manager.register_caught(slug)
        else:
            manager.register_seen(slug)

    if expect_error:
        with pytest.raises(expect_error):
            manager.remove_entry(slug)
        return

    if expected_event == EVENT_MONSTER_REMOVED:
        manager.remove_entry(slug)
    else:
        if status == SeenStatus.CAUGHT:
            manager.register_caught(slug)
        else:
            manager.register_seen(slug)

    if expected_event == EVENT_MONSTER_REMOVED:
        assert slug not in manager.data.entries
    else:
        assert manager.data.get_status(slug) == expected_status
        assert manager.data.get_appearance(slug) == expected_appearance
        assert manager.data.get_caught(slug) == expected_caught

    event_bus.publish.assert_called_with(
        expected_event,
        monster_slug=slug,
        status=expected_status,
        appearance_count=expected_appearance,
        caught_count=expected_caught,
        **(
            {"status_changed": True}
            if expected_event == EVENT_MONSTER_STATUS_UPDATED
            else {}
        ),
    )


@pytest.mark.parametrize(
    "remove_seen_only,expected_total,expected_remaining,expected_removed",
    [
        pytest.param(True, 1, 1, 2, id="only_seen"),
        pytest.param(False, 0, 0, 3, id="all"),
    ],
)
def test_reset(
    manager,
    event_bus,
    remove_seen_only,
    expected_total,
    expected_remaining,
    expected_removed,
):
    manager.register_caught("caught_mon")
    manager.register_seen("seen_mon_1")
    manager.register_seen("seen_mon_2")

    manager.reset(remove_seen_only=remove_seen_only)

    assert manager.data.get_total_monsters() == expected_total
    if remove_seen_only:
        assert manager.data.is_registered("caught_mon")
        assert not manager.data.is_registered("seen_mon_1")

    event_bus.publish.assert_called_with(
        EVENT_TUXEPEDIA_RESET,
        removed_count=expected_removed,
        remaining_count=expected_remaining,
        remove_seen_only=remove_seen_only,
        removed_monsters=ANY,
    )


# TestTuxepediaReporter
@pytest.fixture
def reporter():
    initial_entries = {
        "rockitten": MonsterEntry(SeenStatus.SEEN, 5),
        "nut": MonsterEntry(SeenStatus.CAUGHT, 10),
        "flowey": MonsterEntry(SeenStatus.SEEN, 2),
    }
    data = TuxepediaData(initial_entries)
    return TuxepediaReporter(data)


def test_get_most_frequent_monsters(reporter):
    top_two = reporter.get_most_frequent_monsters(2)
    assert top_two == [("nut", 10), ("rockitten", 5)]


def test_get_monster_status_distribution(reporter):
    distribution = reporter.get_monster_status_distribution()
    assert distribution[SeenStatus.SEEN] == 2
    assert distribution[SeenStatus.CAUGHT] == 1


def test_get_unregistered_monsters(reporter):
    all_slugs = {"rockitten", "nut", "flowey", "ghost"}
    unregistered = reporter.get_unregistered_monsters(all_slugs)
    assert "ghost" in unregistered
    assert "nut" not in unregistered


@pytest.mark.parametrize(
    "total_game,expected_registered,expected_caught",
    [
        pytest.param(10, 3 / 10, 1 / 10, id="total_10"),
        pytest.param(0, 0.0, 0.0, id="total_0"),
    ],
)
def test_completeness_report(
    reporter, total_game, expected_registered, expected_caught
):
    report = reporter.get_completeness_report(total_game)
    assert pytest.approx(report["registered_percent"]) == expected_registered
    assert pytest.approx(report["caught_percent"]) == expected_caught
    assert report["total_game"] == total_game


# TestSerialization
@pytest.mark.parametrize(
    "entries",
    [
        pytest.param(
            {
                "rockitten": {
                    "status": SeenStatus.SEEN,
                    "appearance_count": 1,
                },
                "nut": {"status": SeenStatus.CAUGHT, "appearance_count": 2},
            },
            id="simple",
        ),
        pytest.param(
            {
                "ghost": {"status": SeenStatus.SEEN, "appearance_count": 5},
                "dragon": {
                    "status": SeenStatus.CAUGHT,
                    "appearance_count": 10,
                },
            },
            id="larger",
        ),
        pytest.param(
            {
                "flowey": {"status": SeenStatus.SEEN, "appearance_count": 3},
                "leafy": {"status": SeenStatus.SEEN, "appearance_count": 7},
            },
            id="seen_only",
        ),
    ],
)
def test_encode_decode_roundtrip(entries, event_bus):
    manager = TuxepediaManager(event_bus)
    for slug, info in entries.items():
        for _ in range(info["appearance_count"]):
            if info["status"] == SeenStatus.CAUGHT:
                manager.register_caught(slug)
            else:
                manager.register_seen(slug)

    json_data = encode_tuxepedia(manager)
    new_manager = decode_tuxepedia(json_data, event_bus)

    for slug in manager.data.get_monsters():
        assert new_manager.data.is_registered(slug)
        assert manager.data.get_status(slug) == new_manager.data.get_status(
            slug
        )
        assert manager.data.get_appearance(
            slug
        ) == new_manager.data.get_appearance(slug)
        assert manager.data.get_caught(slug) == new_manager.data.get_caught(
            slug
        )


def test_decode_with_raw_string_status(event_bus):
    json_data = {
        "rockitten": {
            "status": "seen",
            "appearance_count": 2,
            "caught_count": 0,
        }
    }
    manager = decode_tuxepedia(json_data, event_bus)
    entry = manager.data.entries["rockitten"]
    assert isinstance(entry.status, SeenStatus)
    assert entry.status == SeenStatus.SEEN
