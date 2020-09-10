import unittest

from tuxemon.core.tools import round_to_divisible, copy_dict_with_keys


class TestRoundToDivisible(unittest.TestCase):
    def test_round_down(self):
        result = round_to_divisible(1, 16)
        self.assertEqual(result, 0)

    def test_round_up(self):
        result = round_to_divisible(15, 16)
        self.assertEqual(result, 16)

    def test_round_up_if_half(self):
        result = round_to_divisible(24, 16)
        self.assertEqual(result, 32)

    def test_alternate_divisor(self):
        result = round_to_divisible(51, 100)
        self.assertEqual(result, 100)

    def test_return_type_is_int(self):
        result = type(round_to_divisible(0))
        self.assertEqual(result, int)


class TestCopyDictWithKeys(unittest.TestCase):
    def test(self):
        source = {"a": 1, "b": 2, "c": 3}
        keys = ["a", "c"]
        expected = {"a": 1, "c": 3}
        result = copy_dict_with_keys(source, keys)
        self.assertEqual(result, expected)
