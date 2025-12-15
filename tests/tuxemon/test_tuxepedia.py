# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import ANY, Mock

import pytest

from tuxemon.db import SeenStatus
from tuxemon.tuxepedia import (
    EVENT_MONSTER_ADDED,
    EVENT_MONSTER_REMOVED,
    EVENT_MONSTER_STATUS_UPDATED,
    EVENT_TUXEPEDIA_RESET,
    MonsterEntry,
    TuxepediaData,
    TuxepediaManager,
    TuxepediaReporter,
    decode_tuxepedia,
    encode_tuxepedia,
)


# TestMonsterEntry
@pytest.mark.parametrize(
    "initial_status,initial_appearance,update_to,expected_status,expected_appearance,expected_caught",
    [
        # init defaults
        (SeenStatus.seen, 1, None, SeenStatus.seen, 1, 0),
        # update to caught
        (SeenStatus.seen, 1, SeenStatus.caught, SeenStatus.caught, 2, 1),
        # cannot downgrade caught to seen
        (SeenStatus.caught, 1, SeenStatus.seen, SeenStatus.caught, 1, 0),
        # reset entry
        (SeenStatus.caught, 5, "reset", SeenStatus.seen, 1, 0),
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
        "rockitten": MonsterEntry(SeenStatus.seen, 2),
        "nut": MonsterEntry(SeenStatus.caught, 5),
        "flowey": MonsterEntry(SeenStatus.seen, 1),
    }
    return TuxepediaData(initial_entries)


def test_init():
    empty_data = TuxepediaData()
    assert empty_data.entries == {}


@pytest.mark.parametrize(
    "slug,expected_status,expected_appearance,expected_caught,is_registered",
    [
        ("nut", SeenStatus.caught, 5, 0, True),
        ("rockitten", SeenStatus.seen, 2, 0, True),
        ("flowey", SeenStatus.seen, 1, 0, True),
        ("unknown", None, 0, 0, False),
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
        # Case 1: add new entry as seen
        (
            "rockitten",
            SeenStatus.seen,
            EVENT_MONSTER_ADDED,
            SeenStatus.seen,
            1,
            0,
            None,
        ),
        # Case 2: update existing entry to caught
        (
            "rockitten",
            SeenStatus.caught,
            EVENT_MONSTER_STATUS_UPDATED,
            SeenStatus.caught,
            2,
            1,
            None,
        ),
        # Case 3: remove entry
        (
            "nut",
            SeenStatus.caught,
            EVENT_MONSTER_REMOVED,
            SeenStatus.caught,
            1,
            0,
            None,
        ),
        # Case 4: remove non-existent entry (error expected)
        (
            "ghost",
            SeenStatus.seen,
            EVENT_MONSTER_REMOVED,
            SeenStatus.seen,
            0,
            0,
            ValueError,
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
        manager.add_entry(slug, status=SeenStatus.seen)
    elif expected_event == EVENT_MONSTER_REMOVED and expect_error is None:
        manager.add_entry(slug, status=status)

    if expect_error:
        with pytest.raises(expect_error):
            manager.remove_entry(slug)
        return

    if expected_event == EVENT_MONSTER_REMOVED:
        manager.remove_entry(slug)
    else:
        manager.add_entry(slug, status=status)

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
        (True, 1, 1, 2),  # remove only seen monsters
        (False, 0, 0, 3),  # remove all monsters (3 removed)
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
    manager.add_entry("caught_mon", status=SeenStatus.caught)
    manager.add_entry("seen_mon_1")
    manager.add_entry("seen_mon_2")

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
        "rockitten": MonsterEntry(SeenStatus.seen, 5),
        "nut": MonsterEntry(SeenStatus.caught, 10),
        "flowey": MonsterEntry(SeenStatus.seen, 2),
    }
    data = TuxepediaData(initial_entries)
    return TuxepediaReporter(data)


def test_get_most_frequent_monsters(reporter):
    top_two = reporter.get_most_frequent_monsters(2)
    assert top_two == [("nut", 10), ("rockitten", 5)]


def test_get_monster_status_distribution(reporter):
    distribution = reporter.get_monster_status_distribution()
    assert distribution[SeenStatus.seen] == 2
    assert distribution[SeenStatus.caught] == 1


def test_get_unregistered_monsters(reporter):
    all_slugs = {"rockitten", "nut", "flowey", "ghost"}
    unregistered = reporter.get_unregistered_monsters(all_slugs)
    assert "ghost" in unregistered
    assert "nut" not in unregistered


@pytest.mark.parametrize(
    "total_game,expected_registered,expected_caught",
    [
        (10, 3 / 10, 1 / 10),
        (0, 0.0, 0.0),
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
        # Case 1: simple seen + caught
        {
            "rockitten": {"status": SeenStatus.seen, "appearance_count": 1},
            "nut": {"status": SeenStatus.caught, "appearance_count": 2},
        },
        # Case 2: larger counts
        {
            "ghost": {"status": SeenStatus.seen, "appearance_count": 5},
            "dragon": {"status": SeenStatus.caught, "appearance_count": 10},
        },
        # Case 3: only seen monsters
        {
            "flowey": {"status": SeenStatus.seen, "appearance_count": 3},
            "leafy": {"status": SeenStatus.seen, "appearance_count": 7},
        },
    ],
)
def test_encode_decode_roundtrip(entries, event_bus):
    manager = TuxepediaManager(event_bus)
    for slug, info in entries.items():
        for _ in range(info["appearance_count"]):
            manager.add_entry(slug, status=info["status"])

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
