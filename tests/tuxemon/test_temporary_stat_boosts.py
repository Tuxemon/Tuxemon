# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""
Temporary stat boosts are recorded against the monster they affect.

Whatever applies a boost — an item used from the bag, a held item, a
technique aimed at either side of the field, or a status — the monster
reads it back through ``get_combat_stats``.

Step-based modifiers — the ones that move a stage — are shipped by the
five Boost items and by the six techniques in
``STAT_CHANGE_TECHNIQUES`` below. The nine stat-changing statuses
multiply by a value instead, which is a flat addition and never touches
a stage; a stepping status is tested here because the entry point
accepts one, not because content ships one.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
import yaml

from tuxemon.core.core_processor import EffectProcessor
from tuxemon.core.effects.buff import BuffEffect
from tuxemon.core.effects.statchange import (
    StatChangeEffect,
    describe_stage_changes,
    stage_change_message_key,
)
from tuxemon.db import EffectPhase, GenderType, StatModel, StatType
from tuxemon.locale.locale import T
from tuxemon.monster.monster import Monster
from tuxemon.monster.stat_utils import StageChange
from tuxemon.monster.stats import NONLINEAR_TABLE, IndividualValues
from tuxemon.session import Session
from tuxemon.taste import Taste

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ITEM_FOLDER = PROJECT_ROOT / "mods/tuxemon/db/item"
TECHNIQUE_FOLDER = PROJECT_ROOT / "mods/tuxemon/db/technique"

BOOST_ITEMS = {
    "boost_armour": "armour",
    "boost_dodge": "dodge",
    "boost_melee": "melee",
    "boost_ranged": "ranged",
    "boost_speed": "speed",
}

LEVEL = 20


def load_yaml(folder: Path, slug: str) -> dict[str, Any]:
    with (folder / f"{slug}.yaml").open("r", encoding="utf-8") as f:
        data: dict[str, Any] = yaml.safe_load(f)
    return data


def load_item_data(slug: str) -> dict[str, Any]:
    return load_yaml(ITEM_FOLDER, slug)


def load_technique_data(slug: str) -> dict[str, Any]:
    return load_yaml(TECHNIQUE_FOLDER, slug)


def stat_modifiers_from(data: dict[str, Any]) -> dict[str, StatModel]:
    """The stat modifiers content ships with, as the db would build them."""
    modifiers = data.get("stat_modifiers") or {}
    return {stat: StatModel(**values) for stat, values in modifiers.items()}


def stat_modifiers_of(slug: str) -> dict[str, StatModel]:
    return stat_modifiers_from(load_item_data(slug))


class FakeMonsterModel:
    species = "testspecies"
    stage = None
    tags: list[str] = []
    terrains: list[str] = []
    max_moves = 4
    txmn_id = 0
    catch_rate = 100
    upper_catch_resistance = 1.0
    lower_catch_resistance = 1.0
    gender_weights = {GenderType.NEUTER: 1.0}
    types: list[str] = []
    shape = None
    randomly = False
    evolutions: list[Any] = []
    history: list[Any] = []
    moveset: list[Any] = []
    flairs: list[Any] = []
    sprites = None
    sounds = None
    height = 1.0
    weight = 1.0


class FakeSource:
    """Stands in for an item, a technique or a status."""

    def __init__(
        self,
        slug: str,
        stat_modifiers: dict[str, StatModel],
        potency: float = 1.0,
        accuracy: float = 1.0,
    ):
        self.slug = slug
        self.name = slug
        self.stat_modifiers = stat_modifiers
        # only read when the source is used as a technique
        self.potency = potency
        self.accuracy = accuracy


class FakeStatus(FakeSource):
    def __init__(
        self,
        slug: str,
        stat_modifiers: dict[str, StatModel],
        host: Monster,
        phase: EffectPhase = EffectPhase.ON_START,
    ):
        super().__init__(slug, stat_modifiers)
        self.host = host
        self.phase = phase
        self._applied: set[str] = set()

    def has_phase(self, phase: EffectPhase) -> bool:
        return self.phase == phase

    def is_already_applied(self, name: str) -> bool:
        return name in self._applied

    def mark_applied(self, name: str) -> None:
        self._applied.add(name)


def make_monster(monkeypatch, slug: str = "testmon") -> Monster:
    """A monster with plain stats: every stat equals level + coeff."""
    # neutral tastes, so a boost is the only thing moving a stat
    monkeypatch.setattr(Taste, "_tastes", {})
    monkeypatch.setattr(
        Taste, "get", classmethod(lambda cls, slug: cls._tastes.get(slug))
    )
    monkeypatch.setattr(Monster, "_init_assets", lambda self, db_data: None)

    monster = Monster(slug, FakeMonsterModel())
    monster.flair_slugs = set()
    monster.flairs = {}
    monster.individual_values = IndividualValues()
    monster.experience_handler.set_level(LEVEL)
    monster.set_stats()
    monster.current_hp = monster.hp
    return monster


@pytest.fixture
def monster(monkeypatch):
    return make_monster(monkeypatch)


@pytest.fixture
def opponent(monkeypatch):
    return make_monster(monkeypatch, slug="opponent")


@pytest.fixture
def session():
    session = MagicMock(spec=Session)
    # a technique's stat change rolls against this, as "give" does
    session.client.combat_session.get_tech_hit.return_value = 0.0
    return session


def use_item(session, item, target) -> None:
    """Runs an item's statchange effect the way the combat menu does."""
    EffectProcessor([StatChangeEffect()]).process_item(
        session=session, source=item, target=target
    )


# The shipped Boost items


@pytest.mark.parametrize(
    "slug, stat",
    [
        pytest.param(slug, stat, id=f"content_{slug}")
        for slug, stat in BOOST_ITEMS.items()
    ],
)
def test_boost_item_content_targets_its_own_stat(slug, stat):
    data = load_item_data(slug)
    assert [effect["type"] for effect in data["effects"]] == ["statchange"]
    assert list(data["stat_modifiers"]) == [stat]
    assert data["stat_modifiers"][stat]["step"] == 2


@pytest.mark.parametrize(
    "slug, stat",
    [
        pytest.param(slug, stat, id=f"bag_{slug}")
        for slug, stat in BOOST_ITEMS.items()
    ],
)
def test_boost_item_used_from_bag_changes_combat_stats(
    monster, session, slug, stat
):
    """The bug: an item used from the bag never reached the monster."""
    item = FakeSource(slug, stat_modifiers_of(slug))
    before = getattr(monster.get_combat_stats(), stat)

    use_item(session, item, monster)

    after = getattr(monster.get_combat_stats(), stat)
    assert after == before * 2  # two nonlinear stages
    assert monster.get_combat_stats().hp == monster.base_stats.hp


@pytest.mark.parametrize(
    "slug, stat",
    [
        pytest.param(slug, stat, id=f"held_{slug}")
        for slug, stat in BOOST_ITEMS.items()
    ],
)
def test_boost_item_held_changes_combat_stats(monster, session, slug, stat):
    item = FakeSource(slug, stat_modifiers_of(slug))
    monster.item_handler._item = item
    before = getattr(monster.get_combat_stats(), stat)

    use_item(session, item, monster)

    assert getattr(monster.get_combat_stats(), stat) == before * 2


def test_boost_survives_the_item_being_discarded(monster, session):
    """Bag items are consumed after use; the boost outlives them."""
    item = FakeSource("boost_melee", stat_modifiers_of("boost_melee"))
    before = monster.get_combat_stats().melee

    use_item(session, item, monster)
    del item

    assert monster.get_combat_stats().melee == before * 2


# Techniques


def test_technique_boosts_its_user(monster, opponent, session):
    tech = FakeSource(
        "self_buff", {"melee": StatModel(step=2, scaling_mode="nonlinear")}
    )
    session.client.combat_session.get_target_monsters.return_value = [monster]
    before = monster.get_combat_stats().melee

    EffectProcessor([StatChangeEffect(objectives="own_monster")]).process_tech(
        session=session, source=tech, user=monster, target=opponent
    )

    assert monster.get_combat_stats().melee == before * 2
    assert opponent.get_combat_stats().melee == before


def test_technique_debuffs_its_target(monster, opponent, session):
    """The technique writes to the monster it hits, not to itself."""
    tech = FakeSource(
        "enemy_debuff", {"speed": StatModel(step=-2, scaling_mode="nonlinear")}
    )
    session.client.combat_session.get_target_monsters.return_value = [opponent]
    before = opponent.get_combat_stats().speed

    EffectProcessor(
        [StatChangeEffect(objectives="enemy_monster")]
    ).process_tech(session=session, source=tech, user=monster, target=opponent)

    assert opponent.get_combat_stats().speed == before // 2
    assert monster.get_combat_stats().speed == before


def test_technique_stat_change_misses_with_the_technique(
    monster, opponent, session
):
    """A technique that misses does not land its stat change either."""
    tech = FakeSource(
        "enemy_debuff",
        {"speed": StatModel(step=-2, scaling_mode="nonlinear")},
        accuracy=0.8,
    )
    session.client.combat_session.get_tech_hit.return_value = 0.9
    session.client.combat_session.get_target_monsters.return_value = [opponent]
    before = opponent.get_combat_stats().speed

    result = EffectProcessor(
        [StatChangeEffect(objectives="enemy_monster")]
    ).process_tech(session=session, source=tech, user=monster, target=opponent)

    assert not result.success
    assert opponent.get_combat_stats().speed == before
    assert opponent.temporary_stat_boosts.is_empty()


def test_technique_stat_change_needs_objectives(monster, opponent, session):
    tech = FakeSource(
        "no_objectives",
        {"speed": StatModel(step=-2, scaling_mode="nonlinear")},
    )
    before = opponent.get_combat_stats().speed

    result = EffectProcessor([StatChangeEffect()]).process_tech(
        session=session, source=tech, user=monster, target=opponent
    )

    assert not result.success
    assert opponent.get_combat_stats().speed == before


# The techniques that deliver a stat change


STAT_CHANGE_TECHNIQUES = {
    "glower": ("enemy_monster", {"armour": -1}),
    "mudslide": ("enemy_monster", {"speed": -1}),
    "overfeed": ("enemy_monster", {"speed": -2}),
    "sudden_glow": ("own_monster", {"ranged": -1, "dodge": -1}),
    "boulder": ("own_monster", {"armour": 1}),
    "feint": ("own_monster", {"dodge": 1}),
}


@pytest.mark.parametrize(
    "slug, objectives, steps",
    [
        pytest.param(slug, objectives, steps, id=f"content_{slug}")
        for slug, (objectives, steps) in STAT_CHANGE_TECHNIQUES.items()
    ],
)
def test_technique_content_declares_its_stat_change(slug, objectives, steps):
    data = load_technique_data(slug)

    statchange = [e for e in data["effects"] if e["type"] == "statchange"]
    assert len(statchange) == 1, f"{slug} should have one statchange effect"
    assert statchange[0]["parameters"] == [objectives]

    assert data["stat_modifiers"] == {
        stat: {"step": step} for stat, step in steps.items()
    }
    # the roll that gates the stat change
    assert data["potency"] > 0


@pytest.mark.parametrize(
    "slug, objectives, steps",
    [
        pytest.param(slug, objectives, steps, id=f"applies_{slug}")
        for slug, (objectives, steps) in STAT_CHANGE_TECHNIQUES.items()
    ],
)
def test_technique_content_applies_to_the_right_monster(
    monster, opponent, session, slug, objectives, steps
):
    data = load_technique_data(slug)
    tech = FakeSource(
        slug,
        stat_modifiers_from(data),
        potency=data["potency"],
        accuracy=data["accuracy"],
    )
    affected = monster if objectives == "own_monster" else opponent
    bystander = opponent if objectives == "own_monster" else monster
    session.client.combat_session.get_target_monsters.return_value = [affected]

    EffectProcessor([StatChangeEffect(objectives=objectives)]).process_tech(
        session=session, source=tech, user=monster, target=opponent
    )

    for stat, step in steps.items():
        assert affected.temporary_stat_boosts.get_stage(stat) == step
        base = getattr(affected.base_stats, stat)
        expected = int(base * NONLINEAR_TABLE[step])
        assert getattr(affected.get_combat_stats(), stat) == expected

    assert bystander.temporary_stat_boosts.is_empty()


# Statuses


def test_status_boosts_its_host(monster, session):
    status = FakeStatus(
        "status_buff",
        {"armour": StatModel(step=2, scaling_mode="nonlinear")},
        host=monster,
    )
    before = monster.get_combat_stats().armour

    EffectProcessor([StatChangeEffect()]).process_status(
        session=session, source=status
    )

    assert monster.get_combat_stats().armour == before * 2


def test_status_boost_is_withdrawn_when_the_status_ends(monster, session):
    """The status takes back its own stages and leaves the item's alone."""
    status = FakeStatus(
        "status_buff",
        {"armour": StatModel(step=2, scaling_mode="nonlinear")},
        host=monster,
    )
    item = FakeSource("boost_armour", stat_modifiers_of("boost_armour"))
    before = monster.get_combat_stats().armour

    processor = EffectProcessor([StatChangeEffect()])
    processor.process_status(session=session, source=status)
    use_item(session, item, monster)
    # one shared stage: +2 from the status, +2 from the item
    assert monster.temporary_stat_boosts.get_stage("armour") == 4
    assert monster.get_combat_stats().armour == before * 3

    status.phase = EffectPhase.ON_END
    processor.process_status(session=session, source=status)

    assert monster.temporary_stat_boosts.get_stage("armour") == 2
    assert monster.get_combat_stats().armour == before * 2


def test_status_multiplier_is_withdrawn_when_the_status_ends(monster, session):
    """The shipped statuses buff by multiplying, not by stepping."""
    status = FakeStatus(
        "hardshell",
        {"armour": StatModel(value=1.5, step=None, operation="*")},
        host=monster,
    )
    before = monster.get_combat_stats().armour

    processor = EffectProcessor([StatChangeEffect()])
    processor.process_status(session=session, source=status)
    assert monster.get_combat_stats().armour == int(before * 1.5)

    status.phase = EffectPhase.ON_END
    processor.process_status(session=session, source=status)

    assert monster.get_combat_stats().armour == before


# Buff effect


def test_buff_effect_reaches_the_monster(monster, session):
    item = FakeSource("buff_item", {})
    before = monster.get_combat_stats().speed

    EffectProcessor(
        [BuffEffect(statistic=StatType.SPEED, percentage=0.5)]
    ).process_item(session=session, source=item, target=monster)

    assert monster.get_combat_stats().speed == before + int(before * 0.5)


# Stacking and clearing


def test_stages_accumulate_across_two_uses(monster, session):
    item = FakeSource("boost_melee", stat_modifiers_of("boost_melee"))
    before = monster.get_combat_stats().melee

    use_item(session, item, monster)
    assert monster.get_combat_stats().melee == before * 2  # stage 2

    use_item(session, item, monster)
    assert monster.get_combat_stats().melee == before * 3  # stage 4


def test_stages_stop_at_the_max_step_limit(monster, session):
    item = FakeSource("boost_melee", stat_modifiers_of("boost_melee"))
    before = monster.get_combat_stats().melee

    for _ in range(10):
        use_item(session, item, monster)

    # stage 6 is the cap: x4.0, reached after three uses and held there
    assert monster.get_combat_stats().melee == before * 4
    assert monster.temporary_stat_boosts.get_stage("melee") == 6


def test_two_sources_share_one_stage(monster, session):
    """An item stacking on a status is a single stage, not two boosts."""
    item = FakeSource("boost_melee", stat_modifiers_of("boost_melee"))
    status = FakeStatus(
        "status_buff",
        {"melee": StatModel(step=2, scaling_mode="nonlinear")},
        host=monster,
    )
    before = monster.get_combat_stats().melee

    use_item(session, item, monster)
    EffectProcessor([StatChangeEffect()]).process_status(
        session=session, source=status
    )

    assert monster.temporary_stat_boosts.get_stage("melee") == 4
    assert monster.get_combat_stats().melee == before * 3


def test_debuffs_from_two_sources_share_one_stage(monster, opponent, session):
    tech = FakeSource(
        "enemy_debuff", {"speed": StatModel(step=-2, scaling_mode="nonlinear")}
    )
    session.client.combat_session.get_target_monsters.return_value = [opponent]
    before = opponent.get_combat_stats().speed

    processor = EffectProcessor([StatChangeEffect(objectives="enemy_monster")])
    for _ in range(2):
        processor.process_tech(
            session=session, source=tech, user=monster, target=opponent
        )

    assert opponent.temporary_stat_boosts.get_stage("speed") == -4
    assert opponent.get_combat_stats().speed == int(before * (2 / 6))


def test_boosts_clear_at_the_end_of_combat(monster, session):
    item = FakeSource("boost_melee", stat_modifiers_of("boost_melee"))
    status = FakeStatus(
        "status_buff",
        {"armour": StatModel(step=2, scaling_mode="nonlinear")},
        host=monster,
    )
    melee_before = monster.get_combat_stats().melee
    armour_before = monster.get_combat_stats().armour

    use_item(session, item, monster)
    EffectProcessor([StatChangeEffect()]).process_status(
        session=session, source=status
    )
    assert monster.get_combat_stats().melee == melee_before * 2

    monster.end_combat(session)

    assert monster.get_combat_stats().melee == melee_before
    assert monster.get_combat_stats().armour == armour_before
    assert monster.temporary_stat_boosts.is_empty()


def test_boosts_do_not_leak_into_saves(monster, session):
    item = FakeSource("boost_melee", stat_modifiers_of("boost_melee"))
    use_item(session, item, monster)

    assert "temporary_stat_boosts" not in monster.get_state()


# Telling the player what changed
#
# The rendered text depends on a compiled .mo cache that is machine
# dependent, so these assert on the message key and on how many messages
# were produced, never on the words.


@pytest.mark.parametrize(
    "steps, expected",
    [
        pytest.param(1, "combat_state_stat_rose", id="key_rose_1"),
        pytest.param(
            2, "combat_state_stat_rose_greatly", id="key_rose_greatly_2"
        ),
        pytest.param(
            6, "combat_state_stat_rose_greatly", id="key_rose_greatly_6"
        ),
        pytest.param(-1, "combat_state_stat_fell", id="key_fell_1"),
        pytest.param(
            -2, "combat_state_stat_fell_greatly", id="key_fell_greatly_2"
        ),
        pytest.param(
            -6, "combat_state_stat_fell_greatly", id="key_fell_greatly_6"
        ),
    ],
)
def test_stage_change_message_key(steps, expected):
    assert stage_change_message_key(steps) == expected


@pytest.mark.parametrize(
    "steps, key",
    [
        pytest.param(1, "combat_state_stat_rose", id="describe_rose"),
        pytest.param(
            -2, "combat_state_stat_fell_greatly", id="describe_fell_greatly"
        ),
    ],
)
def test_describe_stage_changes_names_the_monster_and_the_stat(
    monster, monkeypatch, steps, key
):
    seen = {}

    def fake_format(text, parameters=None, domain=None):
        seen["key"] = text
        seen["params"] = parameters
        return "formatted"

    monkeypatch.setattr(T, "format", fake_format)
    monkeypatch.setattr(T, "translate", lambda text, domain=None: text)

    messages = describe_stage_changes(monster, [StageChange("melee", steps)])

    assert messages == ["formatted"]
    assert seen["key"] == key
    assert seen["params"] == {"target": monster.name, "stat": "melee"}


def test_describe_stage_changes_skips_stats_that_did_not_move(monster):
    assert describe_stage_changes(monster, []) == []
    assert describe_stage_changes(monster, [StageChange("melee", 0)]) == []


def test_using_a_boost_item_reports_the_change(monster, session):
    item = FakeSource("boost_melee", stat_modifiers_of("boost_melee"))
    result = EffectProcessor([StatChangeEffect()]).process_item(
        session=session, source=item, target=monster
    )
    assert len(result.extras) == 1


def test_a_boost_item_at_the_cap_reports_nothing(monster, session):
    """Three uses reach stage 6; the fourth moves nothing, so says nothing."""
    item = FakeSource("boost_melee", stat_modifiers_of("boost_melee"))
    processor = EffectProcessor([StatChangeEffect()])

    for _ in range(3):
        result = processor.process_item(
            session=session, source=item, target=monster
        )
        assert len(result.extras) == 1

    assert monster.temporary_stat_boosts.get_stage("melee") == 6
    result = processor.process_item(
        session=session, source=item, target=monster
    )
    assert result.extras == []


def test_a_technique_reports_one_message_per_stat(monster, opponent, session):
    """Sudden Glow moves two of the user's stats, so says so twice."""
    data = load_technique_data("sudden_glow")
    tech = FakeSource(
        "sudden_glow",
        stat_modifiers_from(data),
        potency=data["potency"],
        accuracy=data["accuracy"],
    )
    session.client.combat_session.get_target_monsters.return_value = [monster]

    result = EffectProcessor(
        [StatChangeEffect(objectives="own_monster")]
    ).process_tech(session=session, source=tech, user=monster, target=opponent)

    assert len(result.extras) == 2


def test_a_technique_that_misses_reports_nothing(monster, opponent, session):
    tech = FakeSource(
        "enemy_debuff",
        {"speed": StatModel(step=-2, scaling_mode="nonlinear")},
        accuracy=0.8,
    )
    session.client.combat_session.get_tech_hit.return_value = 0.9
    session.client.combat_session.get_target_monsters.return_value = [opponent]

    result = EffectProcessor(
        [StatChangeEffect(objectives="enemy_monster")]
    ).process_tech(session=session, source=tech, user=monster, target=opponent)

    assert result.extras == []
