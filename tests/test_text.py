import collections
import os
import sys
import unittest

# for some test runners that cannot find the tuxemon core
sys.path.insert(0, os.path.join('tuxemon', ))

from tuxemon.core.components.ui import draw


def flatten(it):
    for x in it:
        if isinstance(x, collections.Iterable) and not isinstance(x, str):
            for y in flatten(x):
                yield y
        else:
            yield x


class TextTestCase(unittest.TestCase):
    def test_iterate_letters(self):
        text = "test"
        for i, c in enumerate(draw.iterate_words(text)):
            value = text[:i + 1]
            self.assertEqual(c, value)

    def test_iterate_lines_no_newline(self):
        input = "test"
        expected = ["test"]

        output = list(draw.iterate_lines(input))
        self.assertEqual(expected, output)

    def test_iterate_letters_with_newline(self):
        input = "test\n"
        expected = ["test"]

        output = list(draw.iterate_lines(input))
        self.assertEqual(expected, output)

    def test_iterate_letters_with_multiple_newlines(self):
        input = "test\ntest"
        expected = ["test", "test"]

        output = list(draw.iterate_lines(input))
        self.assertEqual(expected, output)

    def test_iterate_letters_with_multiple_newlines_trailing(self):
        input = "test\ntest\n"
        expected = ["test", "test"]

        output = list(draw.iterate_lines(input))
        self.assertEqual(expected, output)

        # def test_iterate_character_lines(self):
        #     input = "ts\ntt"
        #     expected = [["t", "ts"], ["t", "tt"]]
        #
        #     output = list(flatten(draw.iterate_character_lines(input)))
        #     self.assertEqual(expected, output)

        # def test_constrain_width(self):
        #     input = "tom\nbob"
        #
        #     font = Mock()
        #     font.size = lambda x: (len(x), 1)
        #
        #     expected = ['t', 'o', 'm', 'b', 'o', 'b']
        #     output = list(draw.constrain_width(input, font, 1))
        #     self.assertEqual(expected, output)
        #
        #     expected = ['to', 'm', 'bo', 'b']
        #     output = list(draw.constrain_width(input, font, 2))
        #     self.assertEqual(expected, output)
        #
        #     expected = ['tom', 'bob']
        #     output = list(draw.constrain_width(input, font, 3))
        #     self.assertEqual(expected, output)

        # def test_letterify(self):
        #     draw.test_iter_text(
        #             """Stacks are a subset of trees, which are a subset of DAGs, which are a subset of all\ngraphs. All stacks are trees, all trees are DAGs, but most DAGs\nare not trees, and most trees are not stacks. DAGs do have a topological ordering which will allow you to store them in a stack (for traversal e.g. dependency resolution), but once you cram them into the stack you have lost valuable information. In this case, the ability to navigate between a screen and its parent if it has a prior sibling""",
        #         None, None)
