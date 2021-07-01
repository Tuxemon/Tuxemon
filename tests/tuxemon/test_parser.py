import unittest

from tuxemon.script.parser import P1, P2
from tuxemon.script.tokens import *


class TestParser1(unittest.TestCase):
    def test_split(self):
        parser = P1(["act1", "action1", "arg1"])
        result = list(parser.parse())
        self.assertEqual([ActionNameToken("action1"), ArgumentToken("arg1")], result)


class TestParser2(unittest.TestCase):
    def test_split(self):
        parser = P2([ActionNameToken("action1"), ArgumentToken("arg1")])
        result = list(parser.parse())
        self.assertEqual(None, result)
