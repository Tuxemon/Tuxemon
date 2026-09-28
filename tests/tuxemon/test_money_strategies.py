# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from types import SimpleNamespace

import pytest

from tuxemon.combat.money_strategies import (
    MONEY_METHOD_VARIABLE,
    MoneyMethod,
    calculate_money,
    get_money_method,
)

PLAYER = SimpleNamespace(is_player=True)
TRAINER = SimpleNamespace(is_player=False)


def item(multiplier):
    return SimpleNamespace(money_multiplier=multiplier)


def monster(
    *, owner=PLAYER, held_item=None, fainted=False, level=10, money=1.0
):
    return SimpleNamespace(
        level=level,
        money_modifier=money,
        owner=owner,
        held_item=held_item,
        is_fainted=fainted,
    )


def session_stub(raw):
    session = SimpleNamespace()
    session.player = SimpleNamespace(
        game_variables=SimpleNamespace(
            get=lambda key, default=None: (
                raw if key == MONEY_METHOD_VARIABLE else default
            )
        )
    )
    return session


# get_money_method


@pytest.mark.parametrize(
    "raw, expected",
    [
        pytest.param(
            "conserved", MoneyMethod.CONSERVED, id="conserved_variable"
        ),
        pytest.param(
            "participant_scaled",
            MoneyMethod.PARTICIPANT_SCALED,
            id="participant_scaled_variable",
        ),
        pytest.param(
            None, MoneyMethod.PARTICIPANT_SCALED, id="unset_falls_back"
        ),
        pytest.param(
            "nonsense", MoneyMethod.PARTICIPANT_SCALED, id="junk_falls_back"
        ),
    ],
)
def test_get_money_method(raw, expected):
    assert get_money_method(session_stub(raw)) == expected


def test_calculate_money_defaults_to_participant_scaled():
    loser = monster(owner=TRAINER)
    attackers = [monster(), monster(), monster()]

    assert calculate_money(loser, attackers) == 30


# participant_scaled: the historical formula


@pytest.mark.parametrize(
    "count, expected",
    [
        pytest.param(1, 10, id="one_attacker"),
        pytest.param(2, 20, id="two_attackers"),
        pytest.param(3, 30, id="three_attackers"),
    ],
)
def test_participant_scaled_pays_once_per_attacker(count, expected):
    loser = monster(owner=TRAINER)
    attackers = [monster() for _ in range(count)]

    prize = calculate_money(loser, attackers, MoneyMethod.PARTICIPANT_SCALED)

    assert prize == expected


def test_participant_scaled_skips_fainted_attackers():
    loser = monster(owner=TRAINER)
    attackers = [monster(), monster(fainted=True), monster(fainted=True)]

    prize = calculate_money(loser, attackers, MoneyMethod.PARTICIPANT_SCALED)

    assert prize == 10


def test_participant_scaled_multiplies_both_held_items():
    loser = monster(owner=TRAINER, held_item=item(2.0))
    attackers = [monster(held_item=item(3.0))]

    prize = calculate_money(loser, attackers, MoneyMethod.PARTICIPANT_SCALED)

    assert prize == 60


def test_participant_scaled_ignores_non_player_attackers():
    loser = monster(owner=TRAINER)
    attackers = [monster(), monster(owner=TRAINER), monster(owner=None)]

    prize = calculate_money(loser, attackers, MoneyMethod.PARTICIPANT_SCALED)

    assert prize == 10


# conserved: the bounty belongs to the defeated monster


@pytest.mark.parametrize(
    "count",
    [
        pytest.param(1, id="one_attacker"),
        pytest.param(2, id="two_attackers"),
        pytest.param(3, id="three_attackers"),
    ],
)
def test_conserved_pays_once_however_many_attacked(count):
    loser = monster(owner=TRAINER)
    attackers = [monster() for _ in range(count)]

    prize = calculate_money(loser, attackers, MoneyMethod.CONSERVED)

    assert prize == 10


def test_conserved_pays_when_every_attacker_fainted():
    loser = monster(owner=TRAINER)
    attackers = [monster(fainted=True), monster(fainted=True)]

    prize = calculate_money(loser, attackers, MoneyMethod.CONSERVED)

    assert prize == 10


def test_conserved_takes_the_best_multiplier_not_the_product():
    loser = monster(owner=TRAINER)
    attackers = [monster(held_item=item(2.0)), monster(held_item=item(3.0))]

    prize = calculate_money(loser, attackers, MoneyMethod.CONSERVED)

    assert prize == 30


def test_conserved_ignores_the_losers_held_item():
    loser = monster(owner=TRAINER, held_item=item(2.0))
    attackers = [monster()]

    prize = calculate_money(loser, attackers, MoneyMethod.CONSERVED)

    assert prize == 10


def test_conserved_pays_nothing_for_a_player_owned_loser():
    loser = monster(owner=PLAYER, money=2.0)
    attackers = [monster()]

    assert calculate_money(loser, attackers, MoneyMethod.CONSERVED) == 0


@pytest.mark.parametrize(
    "attackers",
    [
        pytest.param([], id="nobody_fought"),
        pytest.param([monster(owner=TRAINER)], id="only_trainer_monsters"),
        pytest.param([monster(owner=None)], id="only_ownerless_monsters"),
    ],
)
def test_conserved_pays_nothing_without_player_participants(attackers):
    loser = monster(owner=TRAINER)

    assert calculate_money(loser, attackers, MoneyMethod.CONSERVED) == 0
