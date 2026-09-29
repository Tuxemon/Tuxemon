# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from uuid import uuid4

import pytest

from tuxemon.entity.routing import RoutingPolicyRegistry


class FakeMoves:
    def __init__(self, tech_ids=None):
        self.tech_ids = set(tech_ids or [])

    def has_move(self, slug):
        return slug in self.tech_ids

    def has_tech(self, slug):
        return slug in self.tech_ids

    def find_tech_by_id(self, tech_id):
        return tech_id if tech_id in self.tech_ids else None


class FakeMonster:
    def __init__(self, slug="test", name="Test", tech_ids=None):
        self.slug = slug
        self.name = name
        self.instance_id = uuid4()
        self.owner = None

        self.moves = FakeMoves(tech_ids)

    def set_owner(self, owner):
        self.owner = owner

    def __repr__(self):
        return f"<FakeMonster slug={self.slug} name={self.name}>"


class FakeBoxes:
    def __init__(self):
        self.received = []
        self.accept_monsters = True

    def attempt_add_monster(self, monster, policy, kennel):
        if not self.accept_monsters:
            return False
        self.received.append((monster, kennel))
        return True

    def remove_from_box(self, box_type, box_id, obj):
        self.received = [(m, k) for m, k in self.received if m is not obj]


class FakeNPC:
    pass


@pytest.fixture
def default_policy():
    raw = {
        "force_to_box": False,
        "kennel_override": None,
        "locker_override": None,
        "max_party_size": 3,
        "allow_party_addition": True,
        "auto_release_if_box_full": False,
        "auto_discard_if_box_full": False,
        "overflow_kennel": None,
        "overflow_locker": None,
        "max_box_capacity": None,
        "nickname_rules": {},
        "kennel_name_rules": {},
        "locker_name_rules": {},
    }

    RoutingPolicyRegistry._policies["default"] = raw
    return raw


@pytest.fixture
def handler(default_policy, setup_policies):
    from tuxemon.entity.party import PartyHandler

    return PartyHandler(
        monster_boxes=FakeBoxes(),
        owner=FakeNPC(),
        monsters=[],
        party_limit=3,
        routing_policy_name="default",
    )


@pytest.fixture
def setup_policies():
    RoutingPolicyRegistry._policies["default"] = {
        "max_party_size": 3,
        "allow_party_addition": True,
        "nickname_rules": {},
    }
    RoutingPolicyRegistry._policies["restricted"] = {
        "max_party_size": 1,
        "allow_party_addition": True,
        "nickname_rules": {"prefix": "S-", "suffix": "!"},
    }


def test_add_monster_to_party(handler):
    m = FakeMonster()
    handler.add_monster(m)
    assert handler.party_size == 1
    assert handler.monsters[0] is m
    assert m.owner is handler.owner


def test_add_monster_overflow_goes_to_box(handler):
    m1, m2, m3, m4 = FakeMonster(), FakeMonster(), FakeMonster(), FakeMonster()
    handler.add_monster(m1)
    handler.add_monster(m2)
    handler.add_monster(m3)
    handler.add_monster(m4)
    assert handler.party_size == 3
    assert len(handler._monster_boxes.received) == 1
    assert handler._monster_boxes.received[0][0] is m4


def test_find_monster(handler):
    m = FakeMonster(slug="alpha")
    handler.add_monster(m)
    assert handler.find_monster("alpha") is m
    assert handler.find_monster("missing") is None


def test_find_monster_by_id(handler):
    m = FakeMonster()
    handler.add_monster(m)
    assert handler.find_monster_by_id(m.instance_id) is m


def test_find_monster_by_tech_id(handler):
    tech_id = uuid4()
    m = FakeMonster(tech_ids=[tech_id])
    handler.add_monster(m)
    assert handler.find_monster_by_tech_id(tech_id) is m


def test_has_tech(handler):
    m = FakeMonster(tech_ids=["fireball"])
    handler.add_monster(m)
    assert handler.has_tech("fireball") is True
    assert handler.has_tech("missing") is False


def test_switch_monsters(handler):
    m1, m2 = FakeMonster(), FakeMonster()
    handler.add_monster(m1)
    handler.add_monster(m2)
    handler.switch_monsters(0, 1)
    assert handler.monsters == [m2, m1]


def test_switch_monsters_invalid_index(handler):
    m = FakeMonster()
    handler.add_monster(m)
    with pytest.raises(IndexError):
        handler.switch_monsters(0, 5)


def test_replace_monster(handler):
    m1, m2 = FakeMonster(), FakeMonster()
    handler.add_monster(m1)
    assert handler.replace_monster(m1, m2) is True
    assert handler.monsters[0] is m2
    assert m2.owner is handler.owner


def test_release_monster(handler):
    m1, m2 = FakeMonster(), FakeMonster()
    handler.add_monster(m1)
    handler.add_monster(m2)
    assert handler.release_monster(m1) is True
    assert handler.party_size == 1
    assert m1.owner is None


def test_release_last_monster_fails(handler):
    m = FakeMonster()
    handler.add_monster(m)
    assert handler.release_monster(m) is False
    assert handler.party_size == 1


def test_replace_party(handler):
    m1, m2, m3, m4 = FakeMonster(), FakeMonster(), FakeMonster(), FakeMonster()
    handler.replace_party([m1, m2, m3, m4])
    assert handler.party_size == 3
    assert len(handler._monster_boxes.received) == 1
    assert handler._monster_boxes.received[0][0] is m4


def test_transfer_monster_to_box(handler):
    m = FakeMonster()
    handler.add_monster(m)
    assert handler.transfer_monster_to_box(m) is True
    assert handler.party_size == 0
    assert handler._monster_boxes.received[0][0] is m


def test_transfer_monster_to_party(handler):
    m = FakeMonster()
    handler.transfer_monster_to_party(m)
    assert handler.party_size == 1
    assert handler.monsters[0] is m


def test_transfer_to_box_failure_integrity(handler):
    m = FakeMonster()
    handler.add_monster(m)
    handler._monster_boxes.accept_monsters = False
    result = handler.transfer_monster_to_box(m)
    assert result is False
    assert m in handler.monsters
    assert m.owner is handler.owner


def test_nickname_rules_applied(handler):
    m = FakeMonster(name="Tux")
    handler.add_monster(m, override_policy_name="restricted")
    assert m.name == "S-Tux!"


def test_replace_party_cleans_old_owners(handler):
    old_m = FakeMonster()
    handler.add_monster(old_m)
    handler.replace_party([FakeMonster()])
    assert old_m.owner is None


def test_replace_party_with_empty_list(handler):
    handler.add_monster(FakeMonster())
    handler.replace_party([])
    assert handler.party_size == 0


def test_policy_override_on_add(handler):
    m1 = FakeMonster()
    m2 = FakeMonster()
    handler.add_monster(m1, override_policy_name="restricted")
    handler.add_monster(m2, override_policy_name="restricted")
    assert handler.party_size == 1
    assert handler._monster_boxes.received[0][0] is m2


def test_transfer_to_party_fails_when_full(handler):
    for _ in range(3):
        handler.add_monster(FakeMonster())
    m_extra = FakeMonster()
    result = handler.transfer_monster_to_party(m_extra)
    assert result is False
    assert m_extra not in handler.monsters


def test_replace_monster_invalid_old_returns_false(handler):
    m_not_in_party = FakeMonster()
    m_new = FakeMonster()
    result = handler.replace_monster(m_not_in_party, m_new)
    assert result is False


def test_switch_monsters_same_index(handler):
    m = FakeMonster()
    handler.add_monster(m)
    handler.switch_monsters(0, 0)
    assert handler.monsters[0] is m
