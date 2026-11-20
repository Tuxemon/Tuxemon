# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock

import pygame
import pytest

from tuxemon.combat.session import CombatSession
from tuxemon.core.asset import init_assets
from tuxemon.core.core_effect import ItemEffectResult
from tuxemon.db import (
    GenderType,
    ItemBehaviors,
    ItemCategory,
    ItemModel,
    ItemSort,
    LogicCondition,
    Operator,
    ParameterizableRule,
    SoundProperties,
    State,
    StatModel,
    VisualProperties,
)
from tuxemon.entity.bag import BagHandler
from tuxemon.item.item import Item
from tuxemon.monster.monster import Monster
from tuxemon.monster.stats import IndividualValues
from tuxemon.session import Session
from tuxemon.states.monster_menu import MonsterMenuHandler
from tuxemon.taste import Taste
from tuxemon.user_config import CONFIG


@pytest.fixture(autouse=True)
def core_assets():
    """The condition plugins have to be loaded to parse conditions."""
    init_assets()


@pytest.fixture(autouse=True)
def no_sprites(monkeypatch):
    """Items load a sprite on construction; tests don't need the artwork."""
    monkeypatch.setattr(
        "tuxemon.item.item.graphics.load_and_scale",
        lambda *args, **kwargs: pygame.Surface((1, 1)),
    )


_MODELS: dict[str, ItemModel] = {}


@pytest.fixture(autouse=True)
def item_models(monkeypatch):
    """Lets Item.from_save look up the models the tests built."""
    _MODELS.clear()
    monkeypatch.setattr(
        "tuxemon.item.item.ItemModel.lookup",
        classmethod(lambda cls, slug, db: _MODELS[slug]),
    )


@pytest.fixture
def session():
    return MagicMock(spec=Session)


def make_condition(type_: str, *parameters: str, negate: bool = False):
    return LogicCondition(
        type=type_,
        parameters=list(parameters),
        operator=Operator.NOT if negate else Operator.IS,
    )


def make_item(
    slug: str = "potion",
    *,
    holdable: bool = True,
    consumable: bool = False,
    hold_use_conditions=(),
    max_wear: int = 0,
    hold_uses_per_battle: int = 0,
    effects=(),
    stat_modifiers=None,
) -> Item:
    model = ItemModel(
        slug=slug,
        use_item="combat_used_x",
        sort=ItemSort.UTILITY,
        sprite="gfx/items/potion.png",
        category=ItemCategory.NONE,
        usable_in=[State.WorldState],
        behaviors=ItemBehaviors(consumable=consumable, holdable=holdable),
        effects=list(effects),
        stat_modifiers=stat_modifiers or {},
        visuals=VisualProperties(animation=None, flip_axes="", loop=0),
        sound=SoundProperties(sfx=None, volume=0.0),
        modifiers=[],
        conditions=[],
        max_wear=max_wear,
        hold_use_conditions=list(hold_use_conditions),
        hold_uses_per_battle=hold_uses_per_battle,
    )
    _MODELS[slug] = model
    return Item(slug, model)


class FakeDB:
    """The bare minimum a Monster needs from the database."""

    species = "sleek_boulder"
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
    evolutions: list[str] = []
    history: list[str] = []
    moveset: list[str] = []
    flairs: list[str] = []
    sprites = None
    sounds = None
    height = 1.0
    weight = 1.0


@pytest.fixture(autouse=True)
def fake_monster_db(monkeypatch):
    """A real Monster without the database or the artwork behind it."""
    original_init = Monster.__init__

    Taste._tastes = {}

    def fake_init(self, slug="rockat", db_data=None, instance_id=None):
        original_init(self, slug, db_data or FakeDB(), instance_id)

    monkeypatch.setattr(Monster, "__init__", fake_init)
    monkeypatch.setattr(Monster, "_init_assets", lambda self, db_data: None)
    monkeypatch.setattr(
        "tuxemon.monster.monster.MonsterModel.lookup",
        classmethod(lambda cls, slug, db: FakeDB()),
    )


def make_monster(name: str = "Rockat", species: str = "sleek_boulder"):
    mon = Monster()
    mon.name = name
    mon.species = species
    mon.individual_values = IndividualValues()
    mon.base_stats.hp = 100
    mon.current_hp = 100
    return mon


@pytest.fixture
def monster():
    return make_monster()


# --- equipping -----------------------------------------------------------


def test_equip_refused_when_not_holdable(monster):
    item = make_item(holdable=False)

    assert not monster.equip_item(item)
    assert monster.held_item is None


def test_equip_ignores_use_time_conditions(monster):
    """A use-time condition that is false right now still allows equipping."""
    item = make_item(
        hold_use_conditions=[make_condition("current_hp", "<", "0.5")]
    )

    assert monster.hp_ratio == 1.0
    assert monster.equip_item(item)
    assert monster.held_item is item


# --- use-time gate --------------------------------------------------------


def test_validate_held_use_blocks_when_conditions_fail(monster, session):
    item = make_item(
        hold_use_conditions=[make_condition("current_hp", "<", "0.5")]
    )

    assert not item.validate_held_use(session, monster)


def test_validate_held_use_fires_when_conditions_pass(monster, session):
    item = make_item(
        hold_use_conditions=[make_condition("current_hp", "<", "0.5")]
    )
    monster.current_hp = 25

    assert item.validate_held_use(session, monster)


def test_item_with_no_hold_use_conditions_always_fires(monster, session):
    item = make_item()

    assert item.validate_held_use(session, monster)


def make_combat_session(player, monster) -> CombatSession:
    combat = CombatSession()
    combat._players = [player]
    combat.field_monsters.get_monsters = MagicMock(return_value=[monster])
    return combat


def test_check_decisions_skips_held_item_when_gated(monster, session):
    player = MagicMock()
    player.party.is_fainted = False
    item = make_item(
        hold_use_conditions=[make_condition("current_hp", "<", "0.5")]
    )
    monster.equip_item(item)
    item.use = MagicMock()

    make_combat_session(player, monster).check_decisions(session)

    item.use.assert_not_called()


def test_check_decisions_uses_held_item_when_allowed(monster, session):
    player = MagicMock()
    player.party.is_fainted = False
    item = make_item(
        hold_use_conditions=[make_condition("current_hp", "<", "0.5")]
    )
    monster.equip_item(item)
    monster.current_hp = 25
    item.use = MagicMock()

    make_combat_session(player, monster).check_decisions(session)

    item.use.assert_called_once_with(session, player, monster)


# --- feedback -------------------------------------------------------------


def test_firing_announces_itself_and_refreshes_the_hp_bar(monster, session):
    """
    Held items fire in the decision phase, outside the action queue, so the
    redraws that follow a queued action never run for them.
    """
    player = MagicMock()
    player.party.is_fainted = False
    item = make_item(hold_uses_per_battle=1)
    monster.equip_item(item)

    combat = make_combat_session(player, monster)
    combat.event_bus = MagicMock()
    combat.check_decisions(session)

    published = [
        call.args[0] for call in combat.event_bus.publish.call_args_list
    ]
    assert "queue_combat_message" in published
    assert "update_monster_hp" in published


def test_announcement_names_the_monster_and_the_item(monster, session):
    player = MagicMock()
    player.party.is_fainted = False
    item = make_item(hold_uses_per_battle=1)
    monster.equip_item(item)

    combat = make_combat_session(player, monster)
    combat.event_bus = MagicMock()
    combat.check_decisions(session)

    dialog = next(
        call
        for call in combat.event_bus.publish.call_args_list
        if call.args[0] == "queue_combat_message"
    )
    message = dialog.kwargs["message"]
    assert monster.name in message
    assert item.name in message


def test_hp_refresh_names_the_holder(monster, session):
    player = MagicMock()
    player.party.is_fainted = False
    item = make_item()
    monster.equip_item(item)

    combat = make_combat_session(player, monster)
    combat.event_bus = MagicMock()
    combat.check_decisions(session)

    refresh = next(
        call
        for call in combat.event_bus.publish.call_args_list
        if call.args[0] == "update_monster_hp"
    )
    assert refresh.args[1] is monster


def test_a_gated_item_announces_nothing(monster, session):
    player = MagicMock()
    player.party.is_fainted = False
    item = make_item(
        hold_use_conditions=[make_condition("current_hp", "<", "0.5")]
    )
    monster.equip_item(item)

    combat = make_combat_session(player, monster)
    combat.event_bus = MagicMock()
    combat.check_decisions(session)

    combat.event_bus.publish.assert_not_called()


def test_a_permanent_passive_fires_silently(monster, session):
    """
    An item with no gate, no budget and nothing to use up fires every single
    turn purely because it is equipped. The player chose to equip it and can
    see it in the holder's slot, so saying so every turn is only noise. It
    still refreshes the HP bar: a silent item can change hit points.
    """
    player = MagicMock()
    player.party.is_fainted = False
    item = make_item()
    monster.equip_item(item)
    item.use = MagicMock(return_value=ItemEffectResult(success=True))

    combat = make_combat_session(player, monster)
    combat.event_bus = MagicMock()
    combat.check_decisions(session)

    item.use.assert_called_once_with(session, player, monster)
    published = [
        call.args[0] for call in combat.event_bus.publish.call_args_list
    ]
    assert published == ["update_monster_hp"]


def test_two_items_firing_together_queue_both_messages(monster, session):
    """
    In a double battle both holders can fire on the same turn. The messages
    go through the text animation queue so the second doesn't replace the
    first before it has been read.
    """
    player = MagicMock()
    player.party.is_fainted = False
    other = make_monster("Agnite")
    monster.equip_item(make_item("potion", hold_uses_per_battle=1))
    other.equip_item(make_item("tea", hold_uses_per_battle=1))

    combat = CombatSession()
    combat._players = [player]
    combat.field_monsters.get_monsters = MagicMock(
        return_value=[monster, other]
    )
    combat.event_bus = MagicMock()
    combat.check_decisions(session)

    messages = [
        call.kwargs["message"]
        for call in combat.event_bus.publish.call_args_list
        if call.args[0] == "queue_combat_message"
    ]
    assert len(messages) == 2
    assert any(monster.name in m for m in messages)
    assert any(other.name in m for m in messages)


# --- use budget -----------------------------------------------------------


def test_broken_item_does_not_fire(monster, session):
    item = make_item(max_wear=1)
    item.durability.current = 1

    assert item.durability.is_broken
    assert not item.validate_held_use(session, monster)


def test_unbudgeted_item_keeps_firing(monster, session):
    """The default really is unlimited: nothing consumes a held item."""
    player = MagicMock()
    player.party.is_fainted = False
    item = make_item()
    monster.equip_item(item)
    item.use = MagicMock()

    combat = make_combat_session(player, monster)
    for _ in range(3):
        combat.check_decisions(session)

    assert item.use.call_count == 3
    assert monster.held_item is item


def test_item_stops_firing_once_spent(monster, session):
    player = MagicMock()
    player.party.is_fainted = False
    item = make_item(hold_uses_per_battle=2)
    monster.equip_item(item)
    item.use = MagicMock()

    combat = make_combat_session(player, monster)
    for _ in range(4):
        combat.check_decisions(session)

    assert item.use.call_count == 2


def test_spent_item_stays_equipped(monster, session):
    """
    An item that has spent its budget is not used up: it stays with the
    monster so the player doesn't have to re-equip it every battle.
    """
    player = MagicMock()
    player.party.is_fainted = False
    item = make_item(hold_uses_per_battle=1)
    monster.equip_item(item)

    combat = make_combat_session(player, monster)
    combat.check_decisions(session)
    combat.check_decisions(session)

    assert monster.held_item is item
    player.bag.add_item.assert_not_called()


def test_gated_turns_do_not_spend_the_budget(monster, session):
    """Only turns the item actually fires on count against it."""
    player = MagicMock()
    player.party.is_fainted = False
    item = make_item(
        hold_uses_per_battle=1,
        hold_use_conditions=[make_condition("current_hp", "<", "0.5")],
    )
    monster.equip_item(item)
    item.use = MagicMock()

    combat = make_combat_session(player, monster)
    combat.check_decisions(session)
    combat.check_decisions(session)

    item.use.assert_not_called()

    monster.current_hp = 25
    combat.check_decisions(session)
    combat.check_decisions(session)

    item.use.assert_called_once()


def test_budget_refills_for_the_next_battle(monster, session):
    """
    The count lives on the combat session, so it goes away with the battle
    and never has to survive a round trip through the bag.
    """
    player = MagicMock()
    player.party.is_fainted = False
    item = make_item(hold_uses_per_battle=1)
    monster.equip_item(item)
    item.use = MagicMock()

    combat = make_combat_session(player, monster)
    combat.check_decisions(session)
    combat.check_decisions(session)
    assert item.use.call_count == 1

    combat.reset()
    assert not combat._held_item_uses

    combat._players = [player]
    combat.check_decisions(session)
    assert item.use.call_count == 2


def test_two_monsters_have_separate_budgets(monster, session):
    player = MagicMock()
    player.party.is_fainted = False
    other = make_monster("Agnite")
    item_a = make_item("potion", hold_uses_per_battle=1)
    item_b = make_item("tea", hold_uses_per_battle=2)
    monster.equip_item(item_a)
    other.equip_item(item_b)
    item_a.use = MagicMock()
    item_b.use = MagicMock()

    combat = CombatSession()
    combat._players = [player]
    combat.field_monsters.get_monsters = MagicMock(
        return_value=[monster, other]
    )
    combat.check_decisions(session)
    combat.check_decisions(session)

    assert item_a.use.call_count == 1
    assert item_b.use.call_count == 2


# --- swapping -------------------------------------------------------------


def test_swap_items_exchanges_items(monster):
    other = make_monster("Agnite")
    item_a = make_item("potion")
    item_b = make_item("tea")
    monster.equip_item(item_a)
    other.equip_item(item_b)

    monster.swap_items(other)

    assert monster.held_item is item_b
    assert other.held_item is item_a


# --- the item picker must not eat the item --------------------------------


def make_picker_handler() -> MonsterMenuHandler:
    handler = MonsterMenuHandler.__new__(MonsterMenuHandler)
    handler.client = MagicMock()
    handler.party = MagicMock()
    handler.monster_menu = MagicMock()
    return handler


def make_bag(*items: Item) -> BagHandler:
    return BagHandler(MagicMock(), owner=MagicMock(), items=list(items))


def test_picker_removes_item_from_bag_when_equip_succeeds(monster):
    item = make_item()
    handler = make_picker_handler()

    handler._equip_from_picker(monster, MagicMock(game_object=item))

    handler.party.owner.bag.remove_item.assert_called_once_with(item)
    assert monster.held_item is not None
    assert monster.held_item.slug == item.slug


def test_picker_equips_a_separate_copy_of_a_stack(monster):
    stack = make_item(max_wear=5)
    stack.set_quantity(3)
    stack.durability.current = 2
    handler = make_picker_handler()
    handler.party.owner.bag = make_bag(stack)

    handler._equip_from_picker(monster, MagicMock(game_object=stack))

    held = monster.held_item
    assert held is not stack
    assert held.instance_id != stack.instance_id
    assert held.quantity == 1
    assert held.wear == 2
    assert stack.quantity == 2
    assert handler.party.owner.bag.items == [stack]


def test_picker_takes_the_last_copy_out_of_the_bag(monster):
    stack = make_item()
    handler = make_picker_handler()
    handler.party.owner.bag = make_bag(stack)

    handler._equip_from_picker(monster, MagicMock(game_object=stack))

    assert monster.held_item.quantity == 1
    assert handler.party.owner.bag.items == []


def test_picker_leaves_the_bag_alone_when_equip_fails(monster):
    stack = make_item(holdable=False)
    stack.set_quantity(3)
    handler = make_picker_handler()
    handler.party.owner.bag = make_bag(stack)

    handler._equip_from_picker(monster, MagicMock(game_object=stack))

    assert monster.held_item is None
    assert stack.quantity == 3


def test_a_held_item_used_up_does_not_take_another_from_the_bag(
    monster, session
):
    stack = make_heal_item()
    stack.set_quantity(3)
    bag = make_bag(stack)
    handler = make_picker_handler()
    handler.party.owner.bag = bag
    handler._equip_from_picker(monster, MagicMock(game_object=stack))
    monster.current_hp = 10

    player = MagicMock()
    player.party.is_fainted = False
    player.bag = bag
    make_combat_session(player, monster).check_decisions(session)

    assert monster.held_item is None
    assert stack.quantity == 2
    assert bag.items == [stack]


# --- consumption ----------------------------------------------------------


def make_heal_item(slug: str = "moco_berry", **kwargs) -> Item:
    """A consumable held item that really heals, effects and all."""
    return make_item(
        slug,
        consumable=True,
        effects=[
            ParameterizableRule(type="heal", parameters=["0.25", "percentage"])
        ],
        **kwargs,
    )


def test_consumable_item_is_used_up_when_it_fires(monster, session):
    player = MagicMock()
    player.party.is_fainted = False
    item = make_heal_item()
    monster.equip_item(item)
    monster.current_hp = 10

    make_combat_session(player, monster).check_decisions(session)

    assert monster.held_item is None


def test_consumed_item_is_not_given_back_to_the_bag(monster, session):
    """Used up means gone, not returned to the player."""
    player = MagicMock()
    player.party.is_fainted = False
    item = make_heal_item()
    monster.equip_item(item)
    monster.current_hp = 10

    make_combat_session(player, monster).check_decisions(session)

    player.bag.add_item.assert_not_called()


def test_consumable_item_fires_only_once_without_a_budget(monster, session):
    """Being used up is its own limit: no ``hold_uses_per_battle`` needed."""
    player = MagicMock()
    player.party.is_fainted = False
    item = make_heal_item()
    monster.equip_item(item)
    monster.current_hp = 10
    item.use = MagicMock(return_value=ItemEffectResult(success=True))

    combat = make_combat_session(player, monster)
    for _ in range(3):
        combat.check_decisions(session)

    assert item.use.call_count == 1


def test_consumable_item_survives_a_turn_it_cannot_fire(monster, session):
    """A gated item is only used up on the turn it actually fires."""
    player = MagicMock()
    player.party.is_fainted = False
    item = make_heal_item(
        hold_use_conditions=[make_condition("current_hp", "<", "0.5")]
    )
    monster.equip_item(item)

    combat = make_combat_session(player, monster)
    combat.check_decisions(session)

    assert monster.held_item is item

    monster.current_hp = 10
    combat.check_decisions(session)

    assert monster.held_item is None


def test_a_failed_use_still_consumes_by_default(monster, session):
    """Held items answer to the same consumption rule as bagged ones."""
    player = MagicMock()
    player.party.is_fainted = False
    item = make_item(consumable=True)
    monster.equip_item(item)
    item.use = MagicMock(return_value=ItemEffectResult(success=False))

    make_combat_session(player, monster).check_decisions(session)

    assert CONFIG.items_consumed_on_failure
    assert monster.held_item is None


def test_consumed_item_keeps_the_boost_it_applied(monster, session):
    """
    A step boost is recorded against the monster, not the item, so it
    survives the item being used up.
    """
    player = MagicMock()
    player.party.is_fainted = False
    item = make_item(
        "alban_nut",
        consumable=True,
        effects=[ParameterizableRule(type="statchange")],
        stat_modifiers={"melee": StatModel(step=1)},
    )
    monster.base_stats.melee = 20
    monster.equip_item(item)
    unboosted = monster.get_combat_stats().melee

    make_combat_session(player, monster).check_decisions(session)

    assert monster.held_item is None
    assert monster.temporary_stat_boosts.get_stage("melee") > 0
    assert monster.get_combat_stats().melee > unboosted


def test_the_boost_of_a_consumed_item_ends_with_the_battle(monster, session):
    player = MagicMock()
    player.party.is_fainted = False
    item = make_item(
        "alban_nut",
        consumable=True,
        effects=[ParameterizableRule(type="statchange")],
        stat_modifiers={"melee": StatModel(step=1)},
    )
    monster.base_stats.melee = 20
    monster.equip_item(item)

    make_combat_session(player, monster).check_decisions(session)
    monster.clear_all_temporary_boosts()

    assert monster.temporary_stat_boosts.is_empty()


def test_a_replacement_item_gets_its_own_budget(monster, session):
    """
    A consumed item's uses don't carry over to what replaces it.
    """
    player = MagicMock()
    player.party.is_fainted = False
    item = make_heal_item(hold_uses_per_battle=1)
    monster.equip_item(item)
    monster.current_hp = 10

    combat = make_combat_session(player, monster)
    combat.check_decisions(session)

    assert monster.held_item is None
    assert not combat._held_item_uses

    replacement = make_heal_item("mocochinchi", hold_uses_per_battle=1)
    monster.equip_item(replacement)
    combat.check_decisions(session)

    assert monster.held_item is None


def spend_budget(monster, session, item):
    """Equips a non-consumable one-use item and lets it spend its use."""
    player = MagicMock()
    player.party.is_fainted = False
    monster.equip_item(item)
    item.use = MagicMock()
    combat = make_combat_session(player, monster)
    combat.check_decisions(session)
    combat.check_decisions(session)
    assert item.use.call_count == 1
    return combat


def test_an_item_replacing_a_spent_one_gets_its_own_budget(monster, session):
    spent = make_item("potion", hold_uses_per_battle=1)
    combat = spend_budget(monster, session, spent)

    monster.unequip_item()
    replacement = make_item("tea", hold_uses_per_battle=1)
    monster.equip_item(replacement)
    replacement.use = MagicMock()
    combat.check_decisions(session)

    assert replacement.use.call_count == 1


def test_items_swapped_after_one_is_spent_get_their_own_budgets(
    monster, session
):
    spent = make_item("potion", hold_uses_per_battle=1)
    combat = spend_budget(monster, session, spent)

    other = make_monster("Agnite")
    fresh = make_item("tea", hold_uses_per_battle=1)
    other.equip_item(fresh)
    monster.swap_items(other)
    fresh.use = MagicMock()
    combat.check_decisions(session)

    assert monster.held_item is fresh
    assert fresh.use.call_count == 1


def test_the_spent_item_stays_spent_while_still_held(monster, session):
    spent = make_item("potion", hold_uses_per_battle=1)
    combat = spend_budget(monster, session, spent)

    assert combat.get_held_item_uses(monster) == 1


def test_a_non_consumable_item_is_still_never_used_up(monster, session):
    player = MagicMock()
    player.party.is_fainted = False
    item = make_item(consumable=False)
    monster.equip_item(item)

    combat = make_combat_session(player, monster)
    combat.check_decisions(session)

    assert monster.held_item is item


# --- announcement wording -------------------------------------------------


def announced_message(combat) -> str:
    dialog = next(
        call
        for call in combat.event_bus.publish.call_args_list
        if call.args[0] == "queue_combat_message"
    )
    return str(dialog.kwargs["message"])


def test_announcement_says_what_the_item_did(monster, session):
    """
    "Rockat used Moco Berry!" on its own doesn't say what the player got out
    of it, so the item's success line follows, as it does out of the bag.
    """
    player = MagicMock()
    player.party.is_fainted = False
    item = make_heal_item()
    item.use_success = "{target}'s health was restored."
    monster.equip_item(item)
    monster.current_hp = 10

    combat = make_combat_session(player, monster)
    combat.event_bus = MagicMock()
    combat.check_decisions(session)

    message = announced_message(combat)
    assert item.name in message
    assert f"{monster.name}'s health was restored." in message


def test_announcement_prefers_what_the_effect_reported(monster, session):
    """An effect's own line is the specific one, so it wins."""
    player = MagicMock()
    player.party.is_fainted = False
    item = make_item(consumable=True)
    item.use_success = "It worked!"
    monster.equip_item(item)
    item.use = MagicMock(
        return_value=ItemEffectResult(
            success=True, extras=["It was super effective!"]
        )
    )

    combat = make_combat_session(player, monster)
    combat.event_bus = MagicMock()
    combat.check_decisions(session)

    message = announced_message(combat)
    assert "It was super effective!" in message
    assert "It worked!" not in message


def test_announcement_says_when_the_item_failed(monster, session):
    player = MagicMock()
    player.party.is_fainted = False
    item = make_item(hold_uses_per_battle=1)
    item.use_failure = "It failed!"
    monster.equip_item(item)
    item.use = MagicMock(return_value=ItemEffectResult(success=False))

    combat = make_combat_session(player, monster)
    combat.event_bus = MagicMock()
    combat.check_decisions(session)

    assert "It failed!" in announced_message(combat)
