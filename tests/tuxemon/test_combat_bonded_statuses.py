# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock

import pytest

from tuxemon.combat.session import CombatSession
from tuxemon.db import EffectPhase
from tuxemon.monster.status import MonsterStatusHandler


class FakeMonster:
    """Minimal stand-in for a monster taking part in a battle."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.is_fainted = False
        self.status = MonsterStatusHandler()

    def __repr__(self) -> str:
        return f"<FakeMonster {self.name}>"


class FakeParty:
    """Minimal stand-in for a party, for the battlefield-size checks."""

    def __init__(self, npc: "FakeNPC") -> None:
        self._npc = npc

    @property
    def alive(self) -> list[FakeMonster]:
        return [m for m in self._npc.monsters if not m.is_fainted]


class FakeNPC:
    """Minimal stand-in for a trainer owning a party."""

    def __init__(self, name: str, monsters: list[FakeMonster]) -> None:
        self.name = name
        self.monsters = monsters
        self.party = FakeParty(self)

    def __repr__(self) -> str:
        return f"<FakeNPC {self.name}>"


def bond_between(host: FakeMonster, linked: FakeMonster, slug="lifeleech"):
    """Applies a bonded status on the host, linked back to its user."""
    status = MagicMock(slug=slug, bond=True)
    status.host = host
    status.linked_monster = linked
    host.status.add_status(status)
    return status


@pytest.fixture
def session():
    return MagicMock()


@pytest.fixture
def battle():
    """
    Double battle: the player fields A and B (C benched), the opponent
    fields X and Y (Z benched).
    """
    a, b, c = FakeMonster("A"), FakeMonster("B"), FakeMonster("C")
    x, y, z = FakeMonster("X"), FakeMonster("Y"), FakeMonster("Z")
    player = FakeNPC("player", [a, b, c])
    opponent = FakeNPC("opponent", [x, y, z])

    combat = CombatSession()
    combat.set_battle_format(True)
    combat.set_players([player, opponent])
    for npc, monsters in ((player, (a, b)), (opponent, (x, y))):
        for monster in monsters:
            combat.field_monsters.add_monster(npc, monster)

    return {
        "combat": combat,
        "player": player,
        "opponent": opponent,
        "a": a,
        "b": b,
        "c": c,
        "x": x,
        "y": y,
        "z": z,
    }


def withdraw(battle, npc, monster):
    """Takes a monster off the field, as a swap or a faint would."""
    battle["combat"].field_monsters.remove_monster(npc, monster)


def test_unrelated_switch_in_keeps_bond(battle, session):
    """A leeches X: the opponent replacing Y doesn't sever that link."""
    combat, opponent = battle["combat"], battle["opponent"]
    status = bond_between(battle["x"], battle["a"])

    battle["y"].is_fainted = True
    withdraw(battle, opponent, battle["y"])
    combat.add_monster_into_play(session, opponent, battle["z"])

    assert battle["x"].status.get_statuses() == [status]
    status.use.assert_not_called()


def test_withdrawing_the_user_breaks_bond(battle, session):
    """A leeches X: withdrawing A severs the link, X is freed."""
    combat, player = battle["combat"], battle["player"]
    status = bond_between(battle["x"], battle["a"])

    withdraw(battle, player, battle["a"])
    combat.add_monster_into_play(session, player, battle["c"], battle["a"])

    assert battle["x"].status.get_statuses() == []
    status.use.assert_called_once_with(session, EffectPhase.ON_END)


def test_withdrawing_the_host_breaks_bond(battle, session):
    """A leeches X: withdrawing X severs the link, X leaves clean."""
    combat, opponent = battle["combat"], battle["opponent"]
    status = bond_between(battle["x"], battle["a"])

    withdraw(battle, opponent, battle["x"])
    combat.add_monster_into_play(session, opponent, battle["z"], battle["x"])

    assert battle["x"].status.get_statuses() == []
    status.use.assert_called_once_with(session, EffectPhase.ON_END)


def test_bond_doesnt_resume_when_host_returns(battle, session):
    """A bond broken by benching stays broken once the host comes back."""
    combat, opponent = battle["combat"], battle["opponent"]
    bond_between(battle["x"], battle["a"])

    withdraw(battle, opponent, battle["x"])
    combat.add_monster_into_play(session, opponent, battle["z"], battle["x"])

    withdraw(battle, opponent, battle["z"])
    combat.add_monster_into_play(session, opponent, battle["x"], battle["z"])

    assert battle["x"].status.get_statuses() == []


def test_faint_with_no_replacement_still_breaks_bond(battle, session):
    """
    A defeat doesn't always bring a replacement in.

    When the losing side is down to its last monster the battlefield shrinks
    to a single, no switch-in follows, and nothing else would sweep the bond
    the fallen monster was part of.
    """
    combat, opponent = battle["combat"], battle["opponent"]
    status = bond_between(battle["a"], battle["x"], slug="grabbed")

    # the opponent's bench is emptied, so only X and Y can be fielded
    opponent.monsters = [battle["x"], battle["y"]]

    battle["x"].is_fainted = True
    withdraw(battle, opponent, battle["x"])
    assert combat.get_available_positions(opponent) == 0
    assert combat.get_available_positions(battle["player"]) == 0

    combat.clear_broken_bonds(session)

    assert battle["a"].status.get_statuses() == []
    status.use.assert_called_once_with(session, EffectPhase.ON_END)


def test_fainted_participant_breaks_bond(battle, session):
    """A fainted monster is off the battlefield as far as bonds go."""
    combat = battle["combat"]
    status = bond_between(battle["x"], battle["a"])

    battle["a"].is_fainted = True
    combat.clear_broken_bonds(session)

    assert battle["x"].status.get_statuses() == []
    status.use.assert_called_once_with(session, EffectPhase.ON_END)


def test_bond_without_link_is_broken(battle, session):
    """A bonded status that never got a link can never be valid."""
    combat = battle["combat"]
    status = MagicMock(slug="grabbed", bond=True)
    status.host = battle["x"]
    status.linked_monster = None
    battle["x"].status.add_status(status)

    combat.clear_broken_bonds(session)

    assert battle["x"].status.get_statuses() == []
    status.use.assert_called_once_with(session, EffectPhase.ON_END)


def test_intact_bond_survives_repeated_sweeps(battle, session):
    """Sweeping is idempotent, so it can run from several call sites."""
    combat = battle["combat"]
    status = bond_between(battle["x"], battle["a"], slug="grabbed")

    combat.clear_broken_bonds(session)
    combat.clear_broken_bonds(session)

    assert battle["x"].status.get_statuses() == [status]
    status.use.assert_not_called()


def test_broken_bond_is_only_ended_once(battle, session):
    """ON_END fires once, no matter how often the sweep runs."""
    combat, player = battle["combat"], battle["player"]
    status = bond_between(battle["x"], battle["a"], slug="grabbed")

    withdraw(battle, player, battle["a"])
    combat.clear_broken_bonds(session)
    combat.clear_broken_bonds(session)

    status.use.assert_called_once_with(session, EffectPhase.ON_END)


def test_benched_monster_bond_is_swept(battle, session):
    """A bond riding off-field on a benched monster is cleared too."""
    combat, opponent = battle["combat"], battle["opponent"]
    status = bond_between(battle["x"], battle["a"])
    withdraw(battle, opponent, battle["x"])

    combat.clear_broken_bonds(session)

    assert battle["x"].status.get_statuses() == []
    status.use.assert_called_once_with(session, EffectPhase.ON_END)
