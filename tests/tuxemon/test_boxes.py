# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from dataclasses import dataclass
from uuid import uuid4

import pytest

from tuxemon.boxes import BoxMetadata, MonsterBoxes
from tuxemon.entity.routing import RoutingPolicy


@dataclass
class FakeMonster:
    instance_id: str = None
    slug: str = ""

    def __post_init__(self):
        if self.instance_id is None:
            self.instance_id = uuid4()


@pytest.fixture
def monster1():
    return FakeMonster()


@pytest.fixture
def monster2():
    return FakeMonster()


@pytest.fixture
def boxes():
    return MonsterBoxes()


def test_add_monster(boxes, monster1):
    boxes.add_monster("box1", monster1)
    assert "box1" in boxes.monster_boxes
    assert monster1 in boxes.monster_boxes["box1"]


def test_remove_monster(boxes, monster1):
    boxes.add_monster("box1", monster1)
    boxes.remove_from_box("monster", None, monster1)
    assert monster1 not in boxes.monster_boxes["box1"]


def test_remove_monster_from(boxes, monster1):
    boxes.add_monster("box1", monster1)
    boxes.remove_from_box("monster", "box1", monster1)
    assert monster1 not in boxes.monster_boxes["box1"]


def test_get_monsters_by_iid(boxes, monster1):
    boxes.add_monster("box1", monster1)
    assert boxes.get_monsters_by_iid(monster1.instance_id) == monster1


def test_get_monsters(boxes, monster1, monster2):
    boxes.add_monster("box1", monster1)
    boxes.add_monster("box1", monster2)
    assert boxes.get_monsters("box1") == [monster1, monster2]


def test_has_box(boxes, monster1):
    boxes.add_monster("box1", monster1)
    assert boxes.has_box("box1", "monster")


def test_get_box_ids(boxes, monster1, monster2):
    boxes.add_monster("box1", monster1)
    boxes.add_monster("box2", monster2)
    assert boxes.get_box_ids("monster") == ["box1", "box2"]


def test_get_box_size(boxes, monster1, monster2):
    boxes.add_monster("box1", monster1)
    boxes.add_monster("box1", monster2)
    assert boxes.get_box_size("box1", "monster") == 2


def test_get_box_name(boxes, monster1):
    boxes.add_monster("box1", monster1)
    assert boxes.get_box_name(monster1.instance_id) == "box1"


def test_get_all_monsters(boxes, monster1, monster2):
    boxes.add_monster("box1", monster1)
    boxes.add_monster("box2", monster2)
    assert boxes.get_all_monsters() == [monster1, monster2]


def test_get_all_monsters_hidden(boxes, monster1, monster2):
    boxes.create_box("box1", BoxMetadata(max_capacity=10, is_hidden=True))
    boxes.create_box("box2", BoxMetadata(max_capacity=10, is_hidden=False))
    boxes.add_monster("box1", monster1)
    boxes.add_monster("box2", monster2)
    assert boxes.get_all_monsters_hidden() == [monster1]


def test_get_all_monsters_visible(boxes, monster1, monster2):
    boxes.create_box("box1", BoxMetadata(max_capacity=10, is_hidden=True))
    boxes.create_box("box2", BoxMetadata(max_capacity=10, is_hidden=False))
    boxes.add_monster("box1", monster1)
    boxes.add_monster("box2", monster2)
    assert boxes.get_all_monsters_visible() == [monster2]


def test_set_box_hidden_toggle(boxes, monster1):
    boxes.create_box("box1", BoxMetadata(max_capacity=10, is_hidden=False))
    boxes.add_monster("box1", monster1)

    assert boxes.get_all_monsters_visible() == [monster1]

    boxes.set_box_hidden("box1", "monster", True)

    assert boxes.get_all_monsters_hidden() == [monster1]
    assert boxes.get_all_monsters_visible() == []


def test_is_box_full(boxes, monster1):
    boxes.add_monster("box1", monster1)
    policy = RoutingPolicy("default", max_box_capacity=1)
    assert boxes.is_box_full("box1", "monster", policy)

    boxes.remove_from_box("monster", "box1", monster1)
    assert not boxes.is_box_full("box1", "monster", policy)


def test_move_monster(boxes, monster1):
    boxes.add_monster("box1", monster1)
    boxes.move_monster("box1", "box2", monster1)
    assert monster1 in boxes.monster_boxes["box2"]


def test_merge_boxes(boxes, monster1, monster2):
    boxes.add_monster("box1", monster1)
    boxes.add_monster("box1", monster2)
    boxes.merge_and_remove_boxes("box1", "box2")

    assert boxes.get_monsters("box1") == []
    assert boxes.get_monsters("box2") == [monster1, monster2]


def test_create_box(boxes):
    boxes.create_box("box1")
    assert "box1" in boxes.monster_boxes


def test_remove_box_forced(boxes, monster1):
    boxes.create_box("box1")
    boxes.add_monster("box1", monster1)
    boxes.remove_box("box1", force=True)
    assert "box1" not in boxes.monster_boxes


def test_remove_box_not_forced_raises(boxes, monster1):
    boxes.add_monster("box1", monster1)
    with pytest.raises(ValueError):
        boxes.remove_box("box1", force=False)


def test_swap_with_external_monster(boxes, monster1):
    external = FakeMonster()
    boxes.add_monster("box1", monster1)

    swapped = boxes.swap_with_external_monster("box1", monster1, external)

    assert swapped == monster1
    assert boxes.get_monsters("box1") == [external]


def test_swap_with_external_monster_not_found(boxes, monster1):
    external = FakeMonster()
    boxes.add_monster("box1", monster1)

    with pytest.raises(ValueError):
        boxes.swap_with_external_monster("box1", "nonexistent", external)


def test_swap_with_external_monster_invalid_box_id(boxes, monster1):
    external = FakeMonster()
    with pytest.raises(ValueError):
        boxes.swap_with_external_monster("missing", monster1, external)


def test_swap_with_external_monster_by_iid(boxes, monster1):
    external = FakeMonster()
    boxes.add_monster("box1", monster1)

    swapped = boxes.swap_with_external_monster_by_iid(
        monster1.instance_id, external
    )

    assert swapped == monster1
    assert boxes.get_monsters("box1") == [external]


def test_swap_with_external_monster_by_iid_not_found(boxes):
    external = FakeMonster()
    with pytest.raises(ValueError):
        boxes.swap_with_external_monster_by_iid("missing", external)


def test_create_and_merge_box(boxes, monster1):
    for _ in range(10):
        boxes.add_monster("box1", monster1)

    policy = RoutingPolicy("default", max_box_capacity=10)
    assert boxes.is_box_full("box1", "monster", policy)

    boxes.create_and_merge_box("box1", {})

    assert "box11" in boxes.get_box_ids("monster")
    assert len(boxes.get_monsters("box11")) == 10
    assert len(boxes.get_monsters("box1")) == 0


def test_get_total_monster_count(boxes, monster1, monster2):
    boxes.add_monster("box1", monster1)
    boxes.add_monster("box2", monster2)
    assert boxes.get_total_monster_count() == 2


def test_find_monster_by_slug_in_boxes_found(boxes, monster1):
    monster1.slug = "test_slug"
    boxes.add_monster("box1", monster1)
    assert boxes.find_monster_by_slug_in_boxes("test_slug") == (
        "box1",
        monster1,
    )


def test_find_monster_by_slug_in_boxes_not_found(boxes, monster1):
    monster1.slug = "test_slug"
    boxes.add_monster("box1", monster1)
    assert boxes.find_monster_by_slug_in_boxes("other") is None


def test_remove_monsters(boxes, monster1, monster2):
    boxes.add_monster("box1", monster1)
    boxes.add_monster("box2", monster2)
    boxes.remove_monsters([monster1, monster2])
    assert boxes.get_total_monster_count() == 0


def test_remove_box_force_false_empty(boxes):
    boxes.create_box("box1")
    boxes.remove_box("box1")
    assert "box1" not in boxes.monster_boxes


def test_remove_box_force_false_non_empty_raises(boxes, monster1):
    boxes.create_box("box1")
    boxes.add_monster("box1", monster1)
    with pytest.raises(ValueError):
        boxes.remove_box("box1")


def test_remove_box_force_true_non_empty(boxes, monster1):
    boxes.create_box("box1")
    boxes.add_monster("box1", monster1)
    boxes.remove_box("box1", force=True)
    assert "box1" not in boxes.monster_boxes


def test_remove_box_non_existent_raises(boxes):
    with pytest.raises(ValueError):
        boxes.remove_box("does_not_exist")


def test_attempt_add_monster_normal_case(boxes, monster1):
    policy = RoutingPolicy("test", max_box_capacity=5)
    boxes.create_box("box1")

    result = boxes.attempt_add_monster(
        monster1, policy, preferred_kennel="box1"
    )

    assert result
    assert monster1 in boxes.get_monsters("box1")


def test_attempt_add_monster_box_full_with_overflow(boxes, monster1, monster2):
    policy = RoutingPolicy("test", max_box_capacity=1, overflow_kennel="box2")

    boxes.add_monster("box1", monster1)
    boxes.create_box("box2")

    result = boxes.attempt_add_monster(
        monster2, policy, preferred_kennel="box1"
    )

    assert result
    assert monster2 in boxes.get_monsters("box2")


def test_attempt_add_monster_box_full_auto_release(boxes, monster1, monster2):
    policy = RoutingPolicy(
        "test", max_box_capacity=1, auto_release_if_box_full=True
    )

    boxes.add_monster("box1", monster1)
    result = boxes.attempt_add_monster(
        monster2, policy, preferred_kennel="box1"
    )

    assert not result
    assert monster2 not in boxes.get_all_monsters()


def test_attempt_add_monster_overflow_missing_box(boxes, monster1, monster2):
    policy = RoutingPolicy(
        "test", max_box_capacity=1, overflow_kennel="missing"
    )

    boxes.add_monster("box1", monster1)
    result = boxes.attempt_add_monster(
        monster2, policy, preferred_kennel="box1"
    )

    assert not result
    assert monster2 not in boxes.get_all_monsters()


def test_attempt_add_monster_box_full_with_kennel_name_rules(boxes):
    policy = RoutingPolicy(
        name="test",
        max_box_capacity=1,
        kennel_name_rules={"suffix": "extra"},
    )

    m1 = FakeMonster()
    m2 = FakeMonster()

    boxes.add_monster("box1", m1)
    boxes.attempt_add_monster(m2, policy, preferred_kennel="box1")

    created_box_id = "box11extra"
    assert created_box_id in boxes.get_box_ids("monster")

    monsters_in_new_box = boxes.get_monsters(created_box_id)
    assert any(m.instance_id == m2.instance_id for m in monsters_in_new_box)


def test_remove_box_cleans_metadata(boxes):
    boxes.create_box("box1")
    boxes.remove_box("box1")
    assert "box1" not in boxes.metadata_manager._get_dict("monster")


def test_create_box_with_metadata(boxes):
    meta = BoxMetadata(max_capacity=3, is_hidden=True)
    boxes.create_box("box1", meta)

    capacity = boxes.get_max_capacity(
        "box1", "monster", RoutingPolicy("default")
    )
    assert capacity == 3
    assert boxes.is_box_hidden("box1", "monster")


def test_set_box_hidden_and_is_box_hidden(boxes):
    boxes.create_box("box1", BoxMetadata(max_capacity=5, is_hidden=False))

    assert not boxes.is_box_hidden("box1", "monster")

    boxes.set_box_hidden("box1", "monster", True)
    assert boxes.is_box_hidden("box1", "monster")


def test_is_box_full_respects_metadata_capacity(boxes, monster1):
    boxes.create_box("box1", BoxMetadata(max_capacity=1, is_hidden=False))
    boxes.add_monster("box1", monster1)

    policy = RoutingPolicy("default", max_box_capacity=10)
    assert boxes.is_box_full("box1", "monster", policy)


def test_store_party_in_box_success(boxes, monster1, monster2):
    party = [monster1, monster2]
    result = boxes.store_party_in_box("box1", party)
    assert result is True
    assert monster1 in boxes.get_monsters("box1")
    assert monster2 in boxes.get_monsters("box1")
    assert len(party) == 2


def test_store_party_in_box_creates_box_if_missing(boxes, monster1):
    assert not boxes.has_box("box1", "monster")
    boxes.store_party_in_box("box1", [monster1])
    assert boxes.has_box("box1", "monster")


def test_store_party_in_box_creates_metadata(boxes, monster1):
    boxes.store_party_in_box("box1", [monster1], max_size=5)
    meta = boxes.metadata_manager.get("box1", "monster")
    assert meta is not None
    assert meta.max_capacity == 5


def test_store_party_in_box_fails_if_not_enough_space(
    boxes, monster1, monster2
):
    boxes.create_box("box1", BoxMetadata(max_capacity=1, is_hidden=False))
    boxes.add_monster("box1", monster1)
    result = boxes.store_party_in_box("box1", [monster2], max_size=1)
    assert result is False
    assert monster2 not in boxes.get_monsters("box1")


def test_store_party_in_box_does_not_clear_party_on_failure(
    boxes, monster1, monster2
):
    boxes.create_box("box1", BoxMetadata(max_capacity=1, is_hidden=False))
    boxes.add_monster("box1", monster1)
    party = [monster2]
    boxes.store_party_in_box("box1", party, max_size=1)
    assert len(party) == 1


def test_store_party_in_box_existing_box_accumulates(
    boxes, monster1, monster2
):
    boxes.create_box("box1", BoxMetadata(max_capacity=5, is_hidden=False))
    boxes.add_monster("box1", monster1)
    boxes.store_party_in_box("box1", [monster2], max_size=5)
    assert boxes.get_box_size("box1", "monster") == 2


def test_store_party_in_box_empty_party(boxes):
    result = boxes.store_party_in_box("box1", [])
    assert result is True
    assert boxes.get_box_size("box1", "monster") == 0
