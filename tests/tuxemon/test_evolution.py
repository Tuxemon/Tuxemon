# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from tuxemon.db import (
    Acquisition,
    BondComparison,
    Comparison,
    EvolutionStage,
    GameCondition,
    GenderType,
    LearningMethod,
    MonsterEvolutionItemModel,
    MonsterModel,
    PartyConditionsModel,
    StatsComparison,
    StatType,
)
from tuxemon.entity.npc import NPC, PartyHandler
from tuxemon.game_variables import GameVariablesManager
from tuxemon.monster.evolution import Evolution
from tuxemon.monster.monster import Monster
from tuxemon.session import local_session
from tuxemon.technique.technique import Technique


@pytest.fixture
def evolution_context(monkeypatch):
    original_init = Monster.__init__

    def fake_monster_init(
        self, slug="testmon", db_data=None, instance_id=None
    ):
        if db_data is None:
            db_data = MonsterModel.lookup(slug, None)
        original_init(self, slug, db_data, instance_id)

    monkeypatch.setattr(Monster, "__init__", fake_monster_init)
    monkeypatch.setattr(Monster, "_init_assets", lambda self, db_data: None)

    fake_species_data = MagicMock()
    fake_species_data.species = "test"
    fake_species_data.stage = "basic"
    fake_species_data.tags = []
    fake_species_data.terrains = []
    fake_species_data.max_moves = 4
    fake_species_data.txmn_id = 0
    fake_species_data.catch_rate = 100
    fake_species_data.upper_catch_resistance = 1.0
    fake_species_data.lower_catch_resistance = 1.0
    fake_species_data.gender_weights = {GenderType.NEUTER: 1.0}
    fake_species_data.types = []
    fake_species_data.shape = "blob"
    fake_species_data.randomly = False
    fake_species_data.evolutions = []
    fake_species_data.history = []
    tech = MagicMock(spec=Technique, slug="ram")
    fake_species_data.moves = MagicMock()
    fake_species_data.moves.moves = [tech]
    fake_species_data.flairs = set()
    fake_species_data.sprites = MagicMock()
    fake_species_data.sounds = None
    fake_species_data.height = 1.0
    fake_species_data.weight = 1.0

    monkeypatch.setattr(
        MonsterModel, "lookup", lambda slug, db: fake_species_data
    )

    mon = Monster()

    def mock_player_init(self):
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

    with patch.object(NPC, "__init__", mock_player_init):
        local_session.set_player(NPC())
        player = local_session.player
        mon.set_owner(player)

    evo = Evolution(mon)

    yield mon, player, evo


def test_evolve_monster_success(evolution_context):
    mon, player, evo = evolution_context
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
    player.tuxepedia.register_caught = MagicMock()
    evo.evolve_monster(new_mon)
    new_mon.moves.learn_by_method.assert_called_with(
        new_mon, "SpecialBeam", LearningMethod.EVOLUTION
    )
    player.party.replace_monster.assert_called_with(mon, new_mon)
    player.tuxepedia.register_caught.assert_called_with("rockat")


def test_evolve_monster_not_eligible(evolution_context):
    _, _, evo = evolution_context
    new_mon = Monster()
    evo.is_eligible_for_evolution = lambda: False
    new_mon.transfer_properties_from = MagicMock()
    evo.evolve_monster(new_mon)
    new_mon.transfer_properties_from.assert_not_called()


def test_evolve_monster_replace_fails(evolution_context):
    _, player, evo = evolution_context
    new_mon = Monster()
    new_mon.slug = "rockat"
    evo.is_eligible_for_evolution = lambda: True
    new_mon.transfer_properties_from = MagicMock()
    player.party.replace_monster = MagicMock(return_value=False)
    player.tuxepedia = MagicMock()
    evo.evolve_monster(new_mon)
    assert not player.tuxepedia.register_caught.called


def test_no_owner(evolution_context):
    mon, _, _ = evolution_context
    mon.set_owner(None)
    evo = MonsterEvolutionItemModel(monster_slug="rockat")
    context = {"map_inside": True}
    assert not mon.evolution_handler.can_evolve(evo, context)


@pytest.mark.parametrize(
    "level,at_level,expected",
    [
        pytest.param(10, 20, False, id="below_required_level"),
        pytest.param(20, 20, True, id="meets_required_level"),
        pytest.param(20, 20, True, id="all_conditions_met"),
    ],
)
def test_level_requirement(evolution_context, level, at_level, expected):
    mon, _, _ = evolution_context
    mon.set_level(level, level)
    evo = MonsterEvolutionItemModel(monster_slug="rockat", at_level=at_level)
    context = {"map_inside": True}
    assert mon.evolution_handler.can_evolve(evo, context) == expected


@pytest.mark.parametrize(
    "monster_gender,evo_gender,expected",
    [
        pytest.param("male", "female", False, id="gender_mismatch"),
        pytest.param("male", "male", True, id="gender_match"),
    ],
)
def test_gender_conditions(
    evolution_context, monster_gender, evo_gender, expected
):
    mon, _, _ = evolution_context
    mon.gender = monster_gender
    evo = MonsterEvolutionItemModel(monster_slug="rockat", gender=evo_gender)
    context = {"map_inside": True}
    assert mon.evolution_handler.can_evolve(evo, context) == expected


@pytest.mark.parametrize(
    "map_inside,expected",
    [
        pytest.param(False, False, id="inside_mismatch"),
        pytest.param(True, True, id="inside_match"),
    ],
)
def test_inside_conditions(evolution_context, map_inside, expected):
    mon, _, _ = evolution_context
    evo = MonsterEvolutionItemModel(monster_slug="rockat", inside=True)
    context = {"map_inside": map_inside}
    assert mon.evolution_handler.can_evolve(evo, context) == expected


def test_same_monster_slug(evolution_context):
    mon, _, _ = evolution_context
    mon.slug = "rockat"
    evo = MonsterEvolutionItemModel(monster_slug="rockat")
    context = {"map_inside": True}
    assert not mon.evolution_handler.can_evolve(evo, context)


def test_tech_match(evolution_context):
    mon, _, _ = evolution_context
    evo = MonsterEvolutionItemModel(monster_slug="rockat", tech="ram")
    context = {"map_inside": True}
    assert mon.evolution_handler.can_evolve(evo, context)


@pytest.mark.parametrize(
    "monster_acquisition,evo_acquisition,expected",
    [
        pytest.param(
            Acquisition.TRADED, Acquisition.TRADED, True, id="acq_match_traded"
        ),
        pytest.param(
            Acquisition.GIFTED,
            Acquisition.TRADED,
            False,
            id="acq_mismatch_gifted_vs_traded",
        ),
    ],
)
def test_acquisition_conditions(
    evolution_context, monster_acquisition, evo_acquisition, expected
):
    mon, _, _ = evolution_context
    mon.set_acquisition(monster_acquisition)
    evo = MonsterEvolutionItemModel(monster_slug="rockat")
    evo.acquisition = evo_acquisition
    context = {"map_inside": True}
    assert mon.evolution_handler.can_evolve(evo, context) == expected


@pytest.mark.parametrize(
    "taste_attr,taste_value,evo_taste,expected",
    [
        pytest.param(
            "taste_cold",
            "flakey",
            {"cold": "flakey"},
            True,
            id="taste_cold_match",
        ),
        pytest.param(
            "taste_warm",
            "peppy",
            {"warm": "peppy"},
            True,
            id="taste_warm_match",
        ),
        pytest.param(
            "taste_cold",
            "mild",
            {"cold": "flakey"},
            False,
            id="taste_cold_mismatch",
        ),
        pytest.param(
            "taste_warm",
            "peppy",
            {"warm": "salty"},
            False,
            id="taste_warm_mismatch",
        ),
    ],
)
def test_taste_conditions(
    evolution_context, taste_attr, taste_value, evo_taste, expected
):
    mon, _, _ = evolution_context
    setattr(mon, taste_attr, taste_value)
    evo = MonsterEvolutionItemModel(monster_slug="rockat", tastes=evo_taste)
    context = {"map_inside": True}
    assert mon.evolution_handler.can_evolve(evo, context) == expected


@pytest.mark.parametrize(
    "stat_values,comparison,target_stat,expected",
    [
        pytest.param(
            {"hp": 30, "melee": 20},
            Comparison.GREATER_OR_EQUAL,
            StatType.MELEE,
            True,
            id="melee_meets_requirement",
        ),
        pytest.param(
            {"speed": 5, "armour": 10},
            Comparison.GREATER_OR_EQUAL,
            StatType.ARMOUR,
            False,
            id="armour_below_requirement",
        ),
    ],
)
def test_stats_conditions(
    evolution_context, stat_values, comparison, target_stat, expected
):
    mon, _, _ = evolution_context
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
    "variables, player_values, expected",
    [
        pytest.param(
            [{"var": "val"}], {"var": "val"}, True, id="single_var_match"
        ),
        pytest.param(
            [{"var": "val"}],
            {"var": "other_val"},
            False,
            id="single_var_mismatch",
        ),
        pytest.param(
            [{"var1": "val"}, {"var2": "val"}],
            {"var1": "val", "var2": "val"},
            True,
            id="two_vars_both_match",
        ),
        pytest.param(
            [{"var1": "val"}, {"var2": "other_val"}],
            {"var1": "val", "var2": "val"},
            False,
            id="two_vars_one_mismatch",
        ),
    ],
)
def test_variables_conditions(
    evolution_context, variables, player_values, expected
):
    mon, player, _ = evolution_context

    for k, v in player_values.items():
        player.game_variables.set(k, v)

    game_conditions = [
        GameCondition(key=k, value=v)
        for cond in variables
        for k, v in cond.items()
    ]
    evo = MonsterEvolutionItemModel(
        monster_slug="rockat",
        variables=game_conditions,
    )
    context = {"map_inside": True}
    assert mon.evolution_handler.can_evolve(evo, context) == expected


@pytest.mark.parametrize(
    "bond_value,evo_value,expected",
    [
        pytest.param(10, 10, True, id="bond_meets_requirement"),
        pytest.param(5, 10, False, id="bond_below_requirement"),
    ],
)
def test_bond_conditions(evolution_context, bond_value, evo_value, expected):
    mon, _, _ = evolution_context
    mon.bond_handler.bond = bond_value
    evo = MonsterEvolutionItemModel(
        monster_slug="rockat",
        bond=BondComparison(
            comparison=Comparison.GREATER_OR_EQUAL, value=evo_value
        ),
    )
    context = {"map_inside": True}
    assert mon.evolution_handler.can_evolve(evo, context) == expected


@pytest.mark.parametrize(
    "use_item,expected",
    [
        pytest.param(True, True, id="item_used"),
        pytest.param(False, False, id="item_not_used"),
    ],
)
def test_item_conditions(evolution_context, use_item, expected):
    mon, _, _ = evolution_context
    evo = MonsterEvolutionItemModel(
        monster_slug="botbot", item={"booster_tech": 1.0}
    )
    context = {"map_inside": True, "use_item": use_item}
    assert mon.evolution_handler.can_evolve(evo, context) == expected


@pytest.mark.parametrize(
    "monster_type,evo_type,expected",
    [
        pytest.param("metal", "metal", True, id="element_match"),
        pytest.param("metal", "water", False, id="element_mismatch"),
    ],
)
def test_element_conditions(
    evolution_context, monster_type, evo_type, expected
):
    mon, _, _ = evolution_context
    mon.types.set_types([monster_type])
    evo = MonsterEvolutionItemModel(monster_slug="botbot", element=evo_type)
    context = {"map_inside": True}
    assert mon.evolution_handler.can_evolve(evo, context) == expected


@pytest.mark.parametrize(
    "monster_moves,evo_moves,expected",
    [
        pytest.param(["ram"], ["ram"], True, id="moves_match"),
        pytest.param(["ram"], ["strike"], False, id="moves_mismatch"),
    ],
)
def test_moves_conditions(
    evolution_context, monster_moves, evo_moves, expected
):
    mon, _, _ = evolution_context
    mon.moves.moves = [
        MagicMock(spec=Technique, slug=slug) for slug in monster_moves
    ]
    evo = MonsterEvolutionItemModel(monster_slug="rockat", moves=evo_moves)
    context = {"map_inside": True}
    assert mon.evolution_handler.can_evolve(evo, context) == expected


@pytest.mark.parametrize(
    "level,at_level,probability,random_value,expected",
    [
        pytest.param(20, 20, 0.1, 0.05, True, id="level_req_success"),
        pytest.param(20, 20, 0.1, 0.15, False, id="level_req_failure"),
        pytest.param(None, None, 0.1, 0.05, True, id="prob_only_success"),
        pytest.param(None, None, 0.1, 0.15, False, id="prob_only_failure"),
    ],
)
def test_probability_conditions(
    evolution_context,
    monkeypatch,
    level,
    at_level,
    probability,
    random_value,
    expected,
):
    mon, _, _ = evolution_context
    if level is not None:
        mon.set_level(level, level)

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
        pytest.param("potion", "potion", True, id="held_item_match"),
        pytest.param("tea", "potion", False, id="held_item_mismatch"),
        pytest.param(None, "potion", False, id="no_item_held"),
    ],
)
def test_held_item_conditions(
    evolution_context, held_item_slug, evo_item_slug, expected
):
    mon, _, _ = evolution_context

    if held_item_slug is not None:
        item = MagicMock(slug=held_item_slug, granted_statuses=[])
        mon.equip_item(item)

    evo = MonsterEvolutionItemModel(
        monster_slug="rockat",
        held_item=evo_item_slug,
    )

    context = {"map_inside": True}
    assert mon.evolution_handler.can_evolve(evo, context) == expected


@pytest.mark.parametrize(
    "party_slugs,expected",
    [
        pytest.param({"nut": 1}, True, id="party_single_match"),
        pytest.param(
            {"nut": 1, "rockitten": 1}, True, id="party_double_match"
        ),
        pytest.param({"agnidon": 1}, False, id="party_no_match"),
    ],
)
def test_party_conditions(evolution_context, party_slugs, expected):
    mon, _, _ = evolution_context
    evo = MonsterEvolutionItemModel(
        monster_slug="rockat",
        party_conditions=PartyConditionsModel(monster_slugs=party_slugs),
    )
    context = {"map_inside": True}
    assert mon.evolution_handler.can_evolve(evo, context) == expected


@pytest.mark.parametrize(
    "party_alignment,evo_alignment,expected",
    [
        pytest.param("fire", "fire", True, id="alignment_match"),
        pytest.param("water", "fire", False, id="alignment_mismatch"),
    ],
)
def test_party_alignment_conditions(
    evolution_context, party_alignment, evo_alignment, expected
):
    mon, player, _ = evolution_context
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
        pytest.param(
            [GenderType.MALE, GenderType.MALE],
            {GenderType.MALE: 1},
            True,
            id="gender_requirement_met",
        ),
        pytest.param(
            [GenderType.FEMALE, GenderType.FEMALE],
            {GenderType.MALE: 1},
            False,
            id="gender_requirement_not_met",
        ),
    ],
)
def test_party_gender_conditions(
    evolution_context, party_genders, evo_genders, expected
):
    mon, player, _ = evolution_context
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
        pytest.param("earth", {"earth": 1}, True, id="party_type_match"),
        pytest.param("water", {"fire": 1}, False, id="party_type_mismatch"),
    ],
)
def test_party_type_conditions(
    evolution_context, party_type, evo_types, expected
):
    mon, player, _ = evolution_context
    for m in player.party._monsters:
        m.types.set_types([party_type])
    evo = MonsterEvolutionItemModel(
        monster_slug="rockat",
        party_conditions=PartyConditionsModel(monster_types=evo_types),
    )
    context = {"map_inside": True}
    assert mon.evolution_handler.can_evolve(evo, context) == expected


@pytest.mark.parametrize(
    "party_size,evo_size,expected",
    [
        pytest.param(2, 2, True, id="party_size_match"),
        pytest.param(2, 3, False, id="party_size_below"),
    ],
)
def test_party_size_conditions(
    evolution_context, party_size, evo_size, expected
):
    mon, player, _ = evolution_context
    player.party._monsters = player.party._monsters[:party_size]
    evo = MonsterEvolutionItemModel(
        monster_slug="rockat",
        party_conditions=PartyConditionsModel(party_size=evo_size),
    )
    context = {"map_inside": True}
    assert mon.evolution_handler.can_evolve(evo, context) == expected


@pytest.mark.parametrize(
    "levels,evo_level,expected",
    [
        pytest.param([20, 20], 20, True, id="party_level_match"),
        pytest.param([10, 10], 20, False, id="party_level_below"),
    ],
)
def test_party_level_conditions(
    evolution_context, levels, evo_level, expected
):
    mon, player, _ = evolution_context
    for m, level in zip(player.party._monsters, levels):
        m.set_level(level, level)
    evo = MonsterEvolutionItemModel(
        monster_slug="rockat",
        party_conditions=PartyConditionsModel(party_level=evo_level),
    )
    context = {"map_inside": True}
    assert mon.evolution_handler.can_evolve(evo, context) == expected


@pytest.mark.parametrize(
    "stages,evo_stages,expected",
    [
        pytest.param(
            ["basic", "basic"], {"basic": 2}, True, id="party_stages_match"
        ),
        pytest.param(
            ["basic", "basic"],
            {"stage1": 1},
            False,
            id="party_stages_mismatch",
        ),
    ],
)
def test_party_stages_conditions(
    evolution_context, stages, evo_stages, expected
):
    mon, player, _ = evolution_context
    for m, stage in zip(player.party._monsters, stages):
        m.stage = EvolutionStage(stage)
    evo = MonsterEvolutionItemModel(
        monster_slug="rockat",
        party_conditions=PartyConditionsModel(party_stages=evo_stages),
    )
    context = {"map_inside": True}
    assert mon.evolution_handler.can_evolve(evo, context) == expected


def test_returns_valid_evolutions(evolution_context):
    mon, _, evo = evolution_context
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


def test_filters_out_weight_zero(evolution_context):
    mon, _, evo = evolution_context
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


def test_filters_out_ineligible(evolution_context):
    mon, _, evo = evolution_context
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


def test_single_evolution_returns_model(evolution_context):
    _, _, evo = evolution_context
    evo_model = MagicMock(spec=MonsterEvolutionItemModel)
    possible_evolutions = [(evo_model, 1.0)]
    result = evo.choose_evolution_model(possible_evolutions)
    assert result is evo_model


@patch("random.choices")
def test_multiple_evolutions_uses_random_choices(
    mock_choices, evolution_context
):
    _, _, evo = evolution_context
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


def test_empty_evolutions_raises_error(evolution_context):
    _, _, evo = evolution_context
    with pytest.raises(ValueError):
        evo.choose_evolution_model([])


def test_is_valid_evolution_target_true_for_direct(evolution_context):
    _, _, evo = evolution_context
    evo.has_evolution_to = MagicMock(return_value=True)
    evo.has_history_to = MagicMock(return_value=False)
    result = evo.is_valid_evolution_target("slug123")
    assert result


def test_is_valid_evolution_target_true_for_history(evolution_context):
    _, _, evo = evolution_context
    evo.has_evolution_to = MagicMock(return_value=False)
    evo.has_history_to = MagicMock(return_value=True)
    result = evo.is_valid_evolution_target("slug123")
    assert result


def test_is_valid_evolution_target_false(evolution_context):
    _, _, evo = evolution_context
    evo.has_evolution_to = MagicMock(return_value=False)
    evo.has_history_to = MagicMock(return_value=False)
    result = evo.is_valid_evolution_target("slug123")
    assert not result


def test_confirm_pending_evolution_calls_registry_and_resets_flags(
    evolution_context,
):
    mon, _, evo = evolution_context
    registry = MagicMock()
    mon.instance_id = "iid123"
    mon.experience_handler.reset_status_flags = MagicMock()
    evo.confirm_pending_evolution(registry, "slug123")
    registry.clear_missed.assert_called_once_with("iid123", "slug123")
    registry.clear_pending.assert_called_once_with("iid123")
    mon.experience_handler.reset_status_flags.assert_called_once()


def test_deny_pending_evolution_calls_registry_and_resets_flags(
    evolution_context,
):
    mon, _, evo = evolution_context
    registry = MagicMock()
    mon.instance_id = "iid123"
    mon.set_level(10, 10)
    mon.experience_handler.reset_status_flags = MagicMock()
    evo.deny_pending_evolution(registry, "slug123")
    registry.log_missed.assert_called_once_with("iid123", "slug123", 10)
    registry.clear_pending.assert_called_once_with("iid123")
    mon.experience_handler.reset_status_flags.assert_called_once()


def test_get_eligible_evolution_slug_requires_item_but_not_used(
    evolution_context,
):
    mon, player, evo = evolution_context

    evolution_item = MonsterEvolutionItemModel.model_construct(
        monster_slug="rockat", item={"stone": 1}
    )

    mon.evolutions = [evolution_item]
    evo.is_eligible_for_evolution = lambda: True
    evo.can_evolve = lambda item, ctx, owner=None: False
    registry = MagicMock()
    registry.get_blocked.return_value = []
    player.evolution_registry = registry

    type(mon).held_item = PropertyMock(return_value=None)
    slug = evo.get_eligible_evolution_slug(context={"use_item": False})
    assert slug is None


def test_get_eligible_evolution_slug_held_item_blocks(evolution_context):
    mon, player, evo = evolution_context

    evolution_item = MonsterEvolutionItemModel(monster_slug="rockat")
    mon.evolutions = [evolution_item]

    evo.is_eligible_for_evolution = lambda: True
    evo.can_evolve = lambda item, ctx: True

    registry = MagicMock()
    registry.get_blocked.return_value = []
    player.evolution_registry = registry

    blocker = MagicMock()
    blocker.behaviors.block_evolution = True
    type(mon).held_item = PropertyMock(return_value=blocker)
    slug = evo.get_eligible_evolution_slug()
    assert slug is None


def test_get_eligible_evolution_slug_blocked(evolution_context):
    mon, player, evo = evolution_context

    evolution_item = MonsterEvolutionItemModel(monster_slug="rockat")
    mon.evolutions = [evolution_item]

    evo.is_eligible_for_evolution = lambda: True
    evo.can_evolve = lambda item, ctx: True

    registry = MagicMock()
    registry.get_blocked.return_value = ["rockat"]
    player.evolution_registry = registry

    type(mon).held_item = PropertyMock(return_value=None)
    slug = evo.get_eligible_evolution_slug()
    assert slug is None


def test_get_eligible_evolution_slug(evolution_context):
    mon, player, evo = evolution_context

    evolution_item = MonsterEvolutionItemModel.model_construct(
        monster_slug="rockat", item=None
    )
    mon.evolutions = [evolution_item]

    evo.is_eligible_for_evolution = lambda: True
    evo.can_evolve = lambda item, ctx, owner=None: True

    registry = MagicMock()
    registry.get_blocked.return_value = []
    player.evolution_registry = registry

    type(mon).held_item = PropertyMock(return_value=None)
    slug = evo.get_eligible_evolution_slug()
    assert slug == "rockat"
