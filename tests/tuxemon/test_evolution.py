# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from tuxemon.db import (
    Acquisition,
    BondComparison,
    Comparison,
    GenderType,
    LearningMethod,
    MonsterEvolutionItemModel,
    PartyConditionsModel,
    SeenStatus,
    StatsComparison,
    StatType,
)
from tuxemon.game_variables import GameVariablesManager
from tuxemon.monster import Monster
from tuxemon.monster_dir.evolution import Evolution
from tuxemon.npc import PartyHandler
from tuxemon.player import Player
from tuxemon.session import local_session
from tuxemon.technique.technique import Technique


def mockPlayer(self) -> None:
    self.name = "Jeff"
    self._variables = GameVariablesManager()
    member1 = Monster()
    member1.slug = "nut"
    member2 = Monster()
    member2.slug = "rockitten"
    tech = MagicMock(spec=Technique, slug="ram")
    member1.moves.moves = [tech]
    self.party = PartyHandler(MagicMock, self)
    self.party._monsters = [member1, member2]
    self.tuxepedia = MagicMock()


@pytest.fixture
def setup_evolution():
    mon = Monster()
    with patch.object(Player, "__init__", mockPlayer):
        local_session.set_player(Player())
        player = local_session.player
        mon.set_owner(player)
    evo = Evolution(mon)
    return mon, player, evo


def test_evolve_monster_success(setup_evolution):
    mon, player, evo = setup_evolution
    new_mon = Monster()
    new_mon.slug = "rockat"
    move = MagicMock()
    move.learning_method = LearningMethod.EVOLUTION
    move.technique = "SpecialBeam"
    new_mon.moves.moveset = [move]
    evo.is_eligible_for_evolution = lambda: True
    new_mon.transfer_properties_from = MagicMock()
    new_mon.moves.learn_by_method = MagicMock()
    player.party.replace_monster = MagicMock(return_value=True)
    player.tuxepedia.add_entry = MagicMock()
    evo.evolve_monster(new_mon)
    new_mon.transfer_properties_from.assert_called_with(mon)
    new_mon.moves.learn_by_method.assert_called_with(
        new_mon, "SpecialBeam", LearningMethod.EVOLUTION
    )
    player.party.replace_monster.assert_called_with(mon, new_mon)
    player.tuxepedia.add_entry.assert_called_with("rockat", SeenStatus.caught)


def test_evolve_monster_not_eligible(setup_evolution):
    _, _, evo = setup_evolution
    new_mon = Monster()
    evo.is_eligible_for_evolution = lambda: False
    new_mon.transfer_properties_from = MagicMock()
    evo.evolve_monster(new_mon)
    new_mon.transfer_properties_from.assert_not_called()


def test_evolve_monster_replace_fails(setup_evolution):
    _, player, evo = setup_evolution
    new_mon = Monster()
    new_mon.slug = "rockat"
    evo.is_eligible_for_evolution = lambda: True
    new_mon.transfer_properties_from = MagicMock()
    player.party.replace_monster = MagicMock(return_value=False)
    player.tuxepedia = MagicMock()
    evo.evolve_monster(new_mon)
    assert not player.tuxepedia.add_entry.called


def test_no_owner(setup_evolution):
    mon, _, _ = setup_evolution
    mon.set_owner(None)
    evo = MonsterEvolutionItemModel(monster_slug="rockat")
    context = {"map_inside": True}
    assert not mon.evolution_handler.can_evolve(evo, context)


@pytest.mark.parametrize(
    "level,at_level,expected",
    [
        (10, 20, False),  # too low
        (20, 20, True),  # meets requirement
        (20, 20, True),  # part of "all conditions met"
    ],
)
def test_level_requirement(setup_evolution, level, at_level, expected):
    mon, _, _ = setup_evolution
    mon.set_level(level)
    evo = MonsterEvolutionItemModel(monster_slug="rockat", at_level=at_level)
    context = {"map_inside": True}
    assert mon.evolution_handler.can_evolve(evo, context) == expected


@pytest.mark.parametrize(
    "monster_gender,evo_gender,expected",
    [
        ("male", "female", False),
        ("male", "male", True),
    ],
)
def test_gender_conditions(
    setup_evolution, monster_gender, evo_gender, expected
):
    mon, _, _ = setup_evolution
    mon.gender = monster_gender
    evo = MonsterEvolutionItemModel(monster_slug="rockat", gender=evo_gender)
    context = {"map_inside": True}
    assert mon.evolution_handler.can_evolve(evo, context) == expected


@pytest.mark.parametrize(
    "map_inside,expected",
    [
        (False, False),  # mismatch
        (True, True),  # match
    ],
)
def test_inside_conditions(setup_evolution, map_inside, expected):
    mon, _, _ = setup_evolution
    evo = MonsterEvolutionItemModel(monster_slug="rockat", inside=True)
    context = {"map_inside": map_inside}
    assert mon.evolution_handler.can_evolve(evo, context) == expected


def test_same_monster_slug(setup_evolution):
    mon, _, _ = setup_evolution
    mon.slug = "rockat"
    evo = MonsterEvolutionItemModel(monster_slug="rockat")
    context = {"map_inside": True}
    assert not mon.evolution_handler.can_evolve(evo, context)


def test_tech_match(setup_evolution):
    mon, _, _ = setup_evolution
    evo = MonsterEvolutionItemModel(monster_slug="rockat", tech="ram")
    context = {"map_inside": True}
    assert mon.evolution_handler.can_evolve(evo, context)


@pytest.mark.parametrize(
    "monster_acquisition,evo_acquisition,expected",
    [
        (Acquisition.TRADED, Acquisition.TRADED, True),  # match
        (Acquisition.GIFTED, Acquisition.TRADED, False),  # mismatch
    ],
)
def test_acquisition_conditions(
    setup_evolution, monster_acquisition, evo_acquisition, expected
):
    mon, _, _ = setup_evolution
    mon.set_acquisition(monster_acquisition)
    evo = MonsterEvolutionItemModel(monster_slug="rockat")
    evo.acquisition = evo_acquisition
    context = {"map_inside": True}
    assert mon.evolution_handler.can_evolve(evo, context) == expected


@pytest.mark.parametrize(
    "party_slugs,expected",
    [
        ({"nut": 1}, True),  # single match
        ({"nut": 1, "rockitten": 1}, True),  # double match
        ({"agnidon": 1}, False),  # mismatch
    ],
)
def test_party_conditions(setup_evolution, party_slugs, expected):
    mon, _, _ = setup_evolution
    evo = MonsterEvolutionItemModel(
        monster_slug="rockat",
        party_conditions=PartyConditionsModel(monster_slugs=party_slugs),
    )
    context = {"map_inside": True}
    assert mon.evolution_handler.can_evolve(evo, context) == expected


@pytest.mark.parametrize(
    "taste_attr,taste_value,evo_taste,expected",
    [
        ("taste_cold", "flakey", {"cold": "flakey"}, True),
        ("taste_warm", "peppy", {"warm": "peppy"}, True),
        ("taste_cold", "mild", {"cold": "flakey"}, False),
        ("taste_warm", "peppy", {"warm": "salty"}, False),
    ],
)
def test_taste_conditions(
    setup_evolution, taste_attr, taste_value, evo_taste, expected
):
    mon, _, _ = setup_evolution
    setattr(mon, taste_attr, taste_value)
    evo = MonsterEvolutionItemModel(monster_slug="rockat", tastes=evo_taste)
    context = {"map_inside": True}
    assert mon.evolution_handler.can_evolve(evo, context) == expected


@pytest.mark.parametrize(
    "stat_values,comparison,target_stat,expected",
    [
        (
            {"hp": 30, "melee": 20},
            Comparison.greater_or_equal,
            StatType.melee,
            True,
        ),
        (
            {"speed": 5, "armour": 10},
            Comparison.greater_or_equal,
            StatType.armour,
            False,
        ),
    ],
)
def test_stats_conditions(
    setup_evolution, stat_values, comparison, target_stat, expected
):
    mon, _, _ = setup_evolution
    for stat, value in stat_values.items():
        setattr(mon.base_stats, stat, value)
    evo = MonsterEvolutionItemModel(
        monster_slug="rockat",
        stats=StatsComparison(
            stat_type=list(stat_values.keys())[0],
            comparison=comparison,
            target_stat=target_stat,
        ),
    )
    context = {"map_inside": True}
    assert mon.evolution_handler.can_evolve(evo, context) == expected


@pytest.mark.parametrize(
    "variables,player_values,expected",
    [
        ([{"var": "val"}], {"var": "val"}, True),  # single match
        ([{"var": "val"}], {"var": "other_val"}, False),  # single mismatch
        (
            [{"var1": "val"}, {"var2": "val"}],
            {"var1": "val", "var2": "val"},
            True,
        ),  # double match
        (
            [{"var1": "val"}, {"var2": "other_val"}],
            {"var1": "val", "var2": "val"},
            False,
        ),  # double mismatch
    ],
)
def test_variables_conditions(
    setup_evolution, variables, player_values, expected
):
    mon, player, _ = setup_evolution
    for k, v in player_values.items():
        player.game_variables.set(k, v)
    evo = MonsterEvolutionItemModel(monster_slug="rockat", variables=variables)
    context = {"map_inside": True}
    assert mon.evolution_handler.can_evolve(evo, context) == expected


@pytest.mark.parametrize(
    "steps,evo_steps,expected",
    [
        (10, 10, True),  # match
        (5, 10, False),  # mismatch
    ],
)
def test_steps_conditions(setup_evolution, steps, evo_steps, expected):
    mon, _, _ = setup_evolution
    mon.steps = steps
    evo = MonsterEvolutionItemModel(monster_slug="rockat", steps=evo_steps)
    context = {"map_inside": True}
    assert mon.evolution_handler.can_evolve(evo, context) == expected


@pytest.mark.parametrize(
    "bond_value,evo_value,expected",
    [
        (10, 10, True),  # meets requirement
        (5, 10, False),  # below requirement
    ],
)
def test_bond_conditions(setup_evolution, bond_value, evo_value, expected):
    mon, _, _ = setup_evolution
    mon.bond_handler.bond = bond_value
    evo = MonsterEvolutionItemModel(
        monster_slug="rockat",
        bond=BondComparison(
            comparison=Comparison.greater_or_equal, value=evo_value
        ),
    )
    context = {"map_inside": True}
    assert mon.evolution_handler.can_evolve(evo, context) == expected


@pytest.mark.parametrize(
    "use_item,expected",
    [
        (True, True),  # item used
        (False, False),  # item not used
    ],
)
def test_item_conditions(setup_evolution, use_item, expected):
    mon, _, _ = setup_evolution
    evo = MonsterEvolutionItemModel(
        monster_slug="botbot", item={"booster_tech": 1.0}
    )
    context = {"map_inside": True, "use_item": use_item}
    assert mon.evolution_handler.can_evolve(evo, context) == expected


@pytest.mark.parametrize(
    "monster_type,evo_type,expected",
    [
        ("metal", "metal", True),  # match
        ("metal", "water", False),  # mismatch
    ],
)
def test_element_conditions(setup_evolution, monster_type, evo_type, expected):
    mon, _, _ = setup_evolution
    element = MagicMock(slug=monster_type)
    mon.types.set_types([element])
    evo = MonsterEvolutionItemModel(monster_slug="botbot", element=evo_type)
    context = {"map_inside": True}
    assert mon.evolution_handler.can_evolve(evo, context) == expected


@pytest.mark.parametrize(
    "monster_moves,evo_moves,expected",
    [
        (["ram"], ["ram"], True),  # match
        (["ram"], ["strike"], False),  # mismatch
    ],
)
def test_moves_conditions(setup_evolution, monster_moves, evo_moves, expected):
    mon, _, _ = setup_evolution
    mon.moves.moves = [
        MagicMock(spec=Technique, slug=slug) for slug in monster_moves
    ]
    evo = MonsterEvolutionItemModel(monster_slug="rockat", moves=evo_moves)
    context = {"map_inside": True}
    assert mon.evolution_handler.can_evolve(evo, context) == expected


@pytest.mark.parametrize(
    "level,at_level,probability,random_value,expected",
    [
        (20, 20, 0.1, 0.05, True),  # success with level requirement
        (20, 20, 0.1, 0.15, False),  # failure with level requirement
        (None, None, 0.1, 0.05, True),  # success with probability only
        (None, None, 0.1, 0.15, False),  # failure with probability only
    ],
)
def test_probability_conditions(
    setup_evolution,
    monkeypatch,
    level,
    at_level,
    probability,
    random_value,
    expected,
):
    mon, _, _ = setup_evolution
    if level is not None:
        mon.set_level(level)
    evo_kwargs = {"monster_slug": "rockat"}
    if at_level is not None:
        evo_kwargs["at_level"] = at_level
    evo_kwargs["probability"] = probability
    evo = MonsterEvolutionItemModel(**evo_kwargs)
    context = {"map_inside": True}
    monkeypatch.setattr("random.random", lambda: random_value)
    assert mon.evolution_handler.can_evolve(evo, context) == expected


@pytest.mark.parametrize(
    "held_item_slug,evo_item_slug,expected",
    [
        ("potion", "potion", True),  # correct item
        ("tea", "potion", False),  # wrong item
        (None, "potion", False),  # no item held
    ],
)
def test_held_item_conditions(
    setup_evolution, held_item_slug, evo_item_slug, expected
):
    mon, _, _ = setup_evolution
    if held_item_slug is not None:
        item = MagicMock(slug=held_item_slug)
        mon.item_handler.set_item(item)
    evo = MonsterEvolutionItemModel(
        monster_slug="rockat", held_item=evo_item_slug
    )
    context = {"map_inside": True}
    assert mon.evolution_handler.can_evolve(evo, context) == expected


@pytest.mark.parametrize(
    "party_alignment,evo_alignment,expected",
    [
        ("fire", "fire", True),  # match
        ("water", "fire", False),  # mismatch
    ],
)
def test_party_alignment_conditions(
    setup_evolution, party_alignment, evo_alignment, expected
):
    mon, player, _ = setup_evolution
    with patch.object(
        type(player.party), "alignment", new_callable=PropertyMock
    ) as mock_alignment:
        mock_alignment.return_value = party_alignment
        evo = MonsterEvolutionItemModel(
            monster_slug="nut",
            party_conditions=PartyConditionsModel(alignment=evo_alignment),
        )
        context = {"map_inside": True}
        assert mon.evolution_handler.can_evolve(evo, context) == expected


@pytest.mark.parametrize(
    "party_genders,evo_genders,expected",
    [
        (
            [GenderType.male, GenderType.male],
            {GenderType.male: 1},
            True,
        ),  # match
        (
            [GenderType.female, GenderType.female],
            {GenderType.male: 1},
            False,
        ),  # mismatch
    ],
)
def test_party_gender_conditions(
    setup_evolution, party_genders, evo_genders, expected
):
    mon, player, _ = setup_evolution
    for m, gender in zip(player.party._monsters, party_genders):
        m.gender = gender
    evo = MonsterEvolutionItemModel(
        monster_slug="rockat",
        party_conditions=PartyConditionsModel(genders=evo_genders),
    )
    context = {"map_inside": True}
    assert mon.evolution_handler.can_evolve(evo, context) == expected


@pytest.mark.parametrize(
    "party_type,evo_types,expected",
    [
        ("earth", {"earth": 1}, True),  # match
        ("water", {"fire": 1}, False),  # mismatch
    ],
)
def test_party_type_conditions(
    setup_evolution, party_type, evo_types, expected
):
    mon, player, _ = setup_evolution
    element = MagicMock(slug=party_type)
    for m in player.party._monsters:
        m.types.set_types([element])
    evo = MonsterEvolutionItemModel(
        monster_slug="rockat",
        party_conditions=PartyConditionsModel(monster_types=evo_types),
    )
    context = {"map_inside": True}
    assert mon.evolution_handler.can_evolve(evo, context) == expected


def test_returns_valid_evolutions(setup_evolution):
    mon, _, evo = setup_evolution
    item = MagicMock()
    item.slug = "stone"
    evo_model_valid = MagicMock(spec=MonsterEvolutionItemModel)
    evo_model_valid.item = {"stone": 1.0}
    evo_model_valid.monster_slug = "rockat"
    evo_model_invalid = MagicMock(spec=MonsterEvolutionItemModel)
    evo_model_invalid.item = {"other_item": 1.0}
    evo_model_invalid.monster_slug = "nut"
    mon.evolutions = [evo_model_valid, evo_model_invalid]
    evo.can_evolve = MagicMock(return_value=True)
    context = {"use_item": True}
    result = evo.get_possible_item_evolutions(item, context)
    assert len(result) == 1
    assert result[0][0].monster_slug == "rockat"
    assert result[0][1] == 1.0


def test_filters_out_weight_zero(setup_evolution):
    mon, _, evo = setup_evolution
    item = MagicMock()
    item.slug = "stone"
    evo_model = MagicMock(spec=MonsterEvolutionItemModel)
    evo_model.item = {"stone": 0.0}
    evo_model.monster_slug = "rockat"
    mon.evolutions = [evo_model]
    evo.can_evolve = MagicMock(return_value=True)
    context = {"use_item": True}
    result = evo.get_possible_item_evolutions(item, context)
    assert result == []


def test_filters_out_ineligible(setup_evolution):
    mon, _, evo = setup_evolution
    item = MagicMock()
    item.slug = "stone"
    evo_model = MagicMock(spec=MonsterEvolutionItemModel)
    evo_model.item = {"stone": 1.0}
    evo_model.monster_slug = "rockat"
    mon.evolutions = [evo_model]
    evo.can_evolve = MagicMock(return_value=False)
    context = {"use_item": True}
    result = evo.get_possible_item_evolutions(item, context)
    assert result == []


def test_single_evolution_returns_model(setup_evolution):
    _, _, evo = setup_evolution
    evo_model = MagicMock(spec=MonsterEvolutionItemModel)
    possible_evolutions = [(evo_model, 1.0)]
    result = evo.choose_evolution_model(possible_evolutions)
    assert result is evo_model


@patch("random.choices")
def test_multiple_evolutions_uses_random_choices(
    mock_choices, setup_evolution
):
    _, _, evo = setup_evolution
    evo_model1 = MagicMock(spec=MonsterEvolutionItemModel)
    evo_model2 = MagicMock(spec=MonsterEvolutionItemModel)
    possible_evolutions = [(evo_model1, 0.5), (evo_model2, 0.5)]
    mock_choices.return_value = [evo_model2]
    result = evo.choose_evolution_model(possible_evolutions)
    assert result is evo_model2
    mock_choices.assert_called_once()
    args, kwargs = mock_choices.call_args
    assert evo_model1 in args[0]
    assert evo_model2 in args[0]
    assert list(kwargs["weights"]) == [0.5, 0.5]
    assert kwargs["k"] == 1


def test_empty_evolutions_raises_error(setup_evolution):
    _, _, evo = setup_evolution
    with pytest.raises(ValueError):
        evo.choose_evolution_model([])


def test_is_valid_evolution_target_true_for_direct(setup_evolution):
    _, _, evo = setup_evolution
    evo.has_evolution_to = MagicMock(return_value=True)
    evo.has_history_to = MagicMock(return_value=False)
    result = evo.is_valid_evolution_target("slug123")
    assert result


def test_is_valid_evolution_target_true_for_history(setup_evolution):
    _, _, evo = setup_evolution
    evo.has_evolution_to = MagicMock(return_value=False)
    evo.has_history_to = MagicMock(return_value=True)
    result = evo.is_valid_evolution_target("slug123")
    assert result


def test_is_valid_evolution_target_false(setup_evolution):
    _, _, evo = setup_evolution
    evo.has_evolution_to = MagicMock(return_value=False)
    evo.has_history_to = MagicMock(return_value=False)
    result = evo.is_valid_evolution_target("slug123")
    assert not result


def test_confirm_pending_evolution_calls_registry_and_resets_flags(
    setup_evolution,
):
    mon, _, evo = setup_evolution
    registry = MagicMock()
    mon.instance_id = "iid123"
    mon.experience_handler.reset_status_flags = MagicMock()
    evo.confirm_pending_evolution(registry, "slug123")
    registry.clear_missed.assert_called_once_with("iid123", "slug123")
    registry.clear_pending.assert_called_once_with("iid123")
    mon.experience_handler.reset_status_flags.assert_called_once()


def test_deny_pending_evolution_calls_registry_and_resets_flags(
    setup_evolution,
):
    mon, _, evo = setup_evolution
    registry = MagicMock()
    mon.instance_id = "iid123"
    mon.set_level(10)
    mon.experience_handler.reset_status_flags = MagicMock()
    evo.deny_pending_evolution(registry, "slug123")
    registry.log_missed.assert_called_once_with("iid123", "slug123", 10)
    registry.clear_pending.assert_called_once_with("iid123")
    mon.experience_handler.reset_status_flags.assert_called_once()
