import unittest

from tuxemon.core.script.lexer import Lexer


class TestLexer(unittest.TestCase):
    def test_split(self):
        result = Lexer("this is a test").split()
        self.assertEqual(["this", "is", "a", "test"], result)

    def test_whitespace_reduced_and_ignored(self):
        result = Lexer("this    is  a                      test").split()
        self.assertEqual(["this", "is", "a", "test"], result)

    def test_tab_as_whitespace(self):
        result = Lexer("this\tis\ta test").split()
        self.assertEqual(["this", "is", "a", "test"], result)

    def test_as_iterator(self):
        result = Lexer("this is a test").split()
        self.assertEqual(["this", "is", "a", "test"], result)

    def test_as_include_comma(self):
        result = Lexer("this is,a,test").split()
        self.assertEqual(["this", "is,a,test"], result)
