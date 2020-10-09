"""

read all the maps and extract the events from them.
currently used for just testing the parser, but eventually
can be split into tools to syntax check files before
running the game.

"""
from tuxemon.core.script.parser import TestParser1, TestParser2
from tuxemon.core.script.lexer import Lexer
import xml.etree.ElementTree as etree
import glob
import re


class OldParser:

    def parse_line(self, line, hint=None):
        if hint is None:
            pass
        elif hint.startswith("act"):
            return self.parse_action_string(line)
        elif hint.startswith("cond"):
            return self.parse_condition_string(line)
        elif hint.startswith("behav"):
            return self.parse_behav_string(line)

    @staticmethod
    def split_escaped(string_to_split, delim=","):
        """Splits a string by the specified deliminator excluding escaped
        deliminators.

        :param string_to_split: The string to split.
        :param delim: The deliminator to split the string by.

        :type string_to_split: Str
        :type delim: Str

        :rtype: List
        :returns: A list of the splitted string.

        """
        # Split by "," unless it is escaped by a "\"
        split_list = re.split(r'(?<!\\)' + delim, string_to_split)

        # Remove the escape character from the split list
        split_list = [w.replace(r'\,', ',') for w in split_list]

        # strip whitespace around each
        split_list = [i.strip() for i in split_list]

        return split_list

    def parse_action_string(self, text):
        words = text.split(" ", 1)
        act_type = words[0]
        if len(words) > 1:
            args = self.split_escaped(words[1])
        else:
            args = list()
        return act_type, args

    def parse_condition_string(self, text):
        words = text.split(" ", 2)
        operator, cond_type = words[0:2]
        if len(words) > 2:
            args = self.split_escaped(words[2])
        else:
            args = list()
        return operator, cond_type, args

    def parse_behav_string(self, text):
        words = text.split(" ", 1)
        behav_type = words[0]
        if len(words) > 1:
            args = self.split_escaped(words[1])
        else:
            args = list()
        return behav_type, args


old = OldParser()
for filename in glob.glob("mods/tuxemon/maps/*tmx", recursive=True):
    for event, element in etree.iterparse(filename):
        if element.tag == "property":
            name = element.attrib["name"].strip()
            value = element.attrib["value"].strip()
            original = ""
            try:
                original = old.parse_line(value, name)
            except:
                pass
            joined = " " .join((name, value))
            if name.startswith("act") or name.startswith("cond") or name.startswith("act"):
                print("=====================================")
                print("txt |", joined)
                print("old |", original)
                words = Lexer(joined).split()
                print("lex |", words)
                unoriginal = TestParser2(words).as_string()
                print("new |", unoriginal)

                # don't test old dialog actions because they are buggy in the old version
                if not value.startswith("dialog"):
                    assert original == unoriginal
