import unittest

from tuxemon.monster_dir.experience import MonsterExperience
from tuxemon.prepare import MAX_LEVEL


class MockConfig:
    def __init__(self):
        self.experience_groups = {
            "default": {
                "multiplier": 1.0,
                "experience_coefficient": 3,
            },
            "fast": {"multiplier": 0.8, "experience_coefficient": 2.5},
            "slow": {"multiplier": 1.25, "experience_coefficient": 3.5},
        }


mock_config = MockConfig()


class TestMonsterExperience(unittest.TestCase):

    def test_initialization_defaults(self):
        monster = MonsterExperience()
        self.assertEqual(monster.level, 1)
        self.assertEqual(monster.total_experience, 0)
        self.assertEqual(monster.experience_modifier, 1.0)
        self.assertFalse(monster.got_experience)
        self.assertFalse(monster.levelling_up)
        self.assertFalse(monster.is_maxed_out)

    def test_set_level_within_bounds(self):
        monster = MonsterExperience()
        monster.set_level(10)
        self.assertEqual(monster.level, 10)
        self.assertGreater(monster.total_experience, 0)

    def test_set_level_above_max(self):
        monster = MonsterExperience()
        monster.set_level(MAX_LEVEL + 10)
        self.assertEqual(monster.level, MAX_LEVEL)

    def test_experience_required_default_group(self):
        monster = MonsterExperience(level=5)
        required = monster.experience_required()
        expected = 1.0 * (5**3)
        self.assertEqual(required, int(expected))

    def test_experience_required_with_offset(self):
        monster = MonsterExperience(level=5)
        required = monster.experience_required(level_delta=2)
        expected = 1.0 * (7**3)
        self.assertEqual(required, int(expected))

    def test_give_experience_and_level_up(self):
        monster = MonsterExperience(level=1)
        exp_to_next = monster.experience_required(level_delta=1)
        levels_gained = monster.give_experience(exp_to_next)
        self.assertEqual(levels_gained, 1)
        self.assertEqual(monster.level, 2)

    def test_give_experience_to_max_level(self):
        monster = MonsterExperience(level=MAX_LEVEL - 1)
        monster.give_experience(9999999)
        self.assertEqual(monster.level, MAX_LEVEL)
        self.assertTrue(monster.is_maxed_out)

    def test_excess_experience_at_max_level(self):
        monster = MonsterExperience(level=MAX_LEVEL)
        monster._total_experience = monster.experience_required() + 500
        excess = monster.excess_experience()
        self.assertEqual(excess, 500)

    def test_set_exp_group_valid(self):
        monster = MonsterExperience()
        monster.set_exp_group("fast")
        self.assertEqual(monster._exp_group_slug, "fast")

    def test_set_exp_group_invalid(self):
        monster = MonsterExperience()
        with self.assertRaises(ValueError):
            monster.set_exp_group("unknown")

    def test_give_zero_experience(self):
        monster = MonsterExperience(level=1)
        levels_gained = monster.give_experience(0)
        self.assertEqual(levels_gained, 0)
        self.assertEqual(monster.level, 1)

    def test_negative_experience_gain(self):
        monster = MonsterExperience(level=5, total_experience=1000)
        levels_gained = monster.give_experience(-500)
        self.assertEqual(levels_gained, 0)
        self.assertGreaterEqual(monster.total_experience, 0)

    def test_multiple_level_ups(self):
        monster = MonsterExperience(level=1)
        exp_to_level_5 = monster.experience_required(level_delta=4)
        levels_gained = monster.give_experience(exp_to_level_5)
        self.assertEqual(monster.level, 5)
        self.assertEqual(levels_gained, 4)

    def test_experience_required_at_max_level(self):
        monster = MonsterExperience(level=MAX_LEVEL)
        required = monster.experience_required(level_delta=1)
        self.assertGreater(required, 0)
        self.assertTrue(monster.is_maxed_out)

    def test_invalid_exp_group_fallback(self):
        monster = MonsterExperience(level=5)
        monster._exp_group_slug = "nonexistent"
        required = monster.experience_required()
        expected = mock_config.experience_groups["default"]["multiplier"] * (
            5
            ** mock_config.experience_groups["default"][
                "experience_coefficient"
            ]
        )
        self.assertEqual(required, int(expected))

    def test_experience_modifier_applied(self):
        monster = MonsterExperience(level=1)
        monster._experience_modifier = 2.0
        base_exp = monster.experience_required(level_delta=1)
        monster.give_experience(base_exp // 2)
        self.assertEqual(monster.level, 2)

    def test_is_maxed_out_property(self):
        monster_low = MonsterExperience(level=MAX_LEVEL - 1)
        self.assertFalse(monster_low.is_maxed_out)
        monster_max = MonsterExperience(level=MAX_LEVEL)
        self.assertTrue(monster_max.is_maxed_out)
        monster_set = MonsterExperience()
        monster_set.set_level(MAX_LEVEL)
        self.assertTrue(monster_set.is_maxed_out)

    def test_set_level_below_min(self):
        monster = MonsterExperience(level=10)
        monster.set_level(0)
        self.assertEqual(monster.level, 1)
        monster.set_level(-5)
        self.assertEqual(monster.level, 1)

    def test_set_level_resets_progress(self):
        monster = MonsterExperience(level=1)
        exp_for_lvl_4 = monster.experience_required(level_delta=3)
        exp_for_lvl_5 = monster.experience_required(level_delta=4)
        monster._total_experience = exp_for_lvl_5 - 1
        monster.set_level(3)
        expected_exp = monster.experience_required()  # Should be for level 3
        expected_calc = 1.0 * (3**3)
        self.assertEqual(monster.level, 3)
        self.assertEqual(monster.total_experience, int(expected_calc))
        self.assertEqual(monster.total_experience, expected_exp)

    def test_experience_required_slow_group(self):
        monster = MonsterExperience(level=5, exp_group_slug="slow")
        monster.config_monster = mock_config
        required = monster.experience_required()
        expected = 1.25 * (5**3.5)
        self.assertEqual(required, int(expected))

    def test_experience_required_fast_group(self):
        monster = MonsterExperience(level=10, exp_group_slug="fast")
        monster.config_monster = mock_config
        required = monster.experience_required(level_delta=-1)
        expected = 0.8 * (9**2.5)
        self.assertEqual(required, int(expected))

    def test_level_up_flag_set(self):
        monster = MonsterExperience(level=1)
        self.assertFalse(monster.levelling_up)
        exp_to_next = monster.experience_required(level_delta=1)
        monster.give_experience(exp_to_next - monster.total_experience + 1)
        self.assertTrue(monster.levelling_up)

    def test_excess_experience_not_maxed_out(self):
        monster = MonsterExperience(level=10)
        req_for_10 = monster.experience_required()
        monster._total_experience = req_for_10 + 500
        if monster.level < MAX_LEVEL:
            excess = monster.excess_experience()
            self.assertEqual(excess, 0)

    def test_trigger_experience_flags_sets_both(self):
        monster = MonsterExperience()
        monster.trigger_experience_flags()
        self.assertTrue(monster.got_experience)
        self.assertTrue(monster.levelling_up)
