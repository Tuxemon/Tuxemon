"""

Parse the Tuxemon script syntax

reader - pull bytes from a stream

tokenizer - read sth and emit tokens
parser - read tokens and emit game script


parsing here is only for each line...
the encapsulation (lined file, yaml, dict, xml) differs so much

reader - LineReader, DictReader, TiledMapReader
tokenizer - read lines, emit words
parser - emit script

There is no embedded grammar for arguments, it is up to each method to handle it.

"""
import logging
import re
from natsort import natsorted
from tuxemon.core.event import EventObject, MapAction, MapCondition
from tuxemon.core.script.lexer import *
from tuxemon.core.script.tokens import *
from tuxemon.lib.simplefsm import SimpleFSM

logger = logging.getLogger(__name__)


class State:
    EVENT = 1
    ACTION = 2
    CONDITION = 3
    ACTION_NAME = 4
    CONDITION_NAME = 5
    ARGUMENTS = 6


class Parser:

    def load_event(self, obj, tile_size):
        """ Load an Event from the map

        :param obj:
        :param tile_size:
        :rtype: EventObject
        """
        conds = []
        acts = []
        x = int(obj.x / tile_size[0])
        y = int(obj.y / tile_size[1])
        w = int(obj.width / tile_size[0])
        h = int(obj.height / tile_size[1])


class DictReader:
    def read(self, obj):
        # Conditions & actions are stored as Tiled properties.
        # We need to sort them by name, so that "act1" comes before "act2" and so on..
        for key, value in natsorted(obj.properties.items()):
            if key.startswith("cond"):
                operator, cond_type, args = parse_condition_string(value)
                condition = MapCondition(cond_type, args, x, y, w, h, operator, key)
                conds.append(condition)
            elif key.startswith("act"):
                act_type, args = parse_action_string(value)
                action = MapAction(act_type, args, key)
                acts.append(action)

        keys = natsorted(obj.properties.keys())
        for key in keys:
            if key.startswith("behav"):
                behav_string = obj.properties[key]
                behav_type, args = parse_behav_string(behav_string)
                if behav_type == "talk":
                    conds.insert(
                        0, MapCondition("to_talk", args, x, y, w, h, "is", key)
                    )
                    acts.insert(0, MapAction("npc_face", [args[0], "player"], key))
                else:
                    raise Exception

        # add a player_facing_tile condition automatically
        if obj.type == "interact":
            cond_data = MapCondition(
                "player_facing_tile", list(), x, y, w, h, "is", None
            )
            logger.debug(cond_data)
            conds.append(cond_data)

        return EventObject(obj.id, obj.name, x, y, w, h, conds, acts)


class TestParser1:
    """
    needs events like word, whitespace, comma, quote, etc
    yields game events
    """
    # combine all args into a single arg; don't split at whitespace
    treat_args_as_single = ["dialog", "dialog_chain", "music_playing", "play_music"]

    def __init__(self, words):
        self.words = words
        self.state = State.EVENT

    def parse(self):
        for word in self.words:
            for token in self.parse_word(word):
                yield token

    def as_string(self):
        tokens = list(self.parse())
        types = {type(i) for i in tokens}
        if ActionNameToken in types:
            if tokens[0].value in self.treat_args_as_single:
                return tokens[0].value, [" ".join([i.value for i in tokens[1:]])]
            return tokens[0].value, [i.value for i in tokens[1:]]
        if ConditionNameToken in types:
            if tokens[1].value in self.treat_args_as_single:
                return tokens[0].value, tokens[1].value, [" ".join([i.value for i in tokens[2:]])]
            return tokens[0].value, tokens[1].value, [i.value for i in tokens[2:]]
        raise ValueError

    def parse_word(self, word):
        if self.state == State.EVENT:
            if word.startswith("act"):
                name, prio = re.match(r"(\D+)\s*(\d+)", word).groups()
                # yield ActionNameToken(name)
                # yield PriorityToken(prio)
                self.state = State.ACTION
            elif word.startswith("cond"):
                name, prio = re.match(r"(\D+)(\d+)", word).groups()
                # yield ConditionNameToken(name)
                # yield PriorityToken(prio)
                self.state = State.CONDITION
            else:
                raise ValueError("cannot parse")
        elif self.state == State.ACTION:
            yield ActionNameToken(word)
            self.state = State.ARGUMENTS
        elif self.state == State.CONDITION:
            yield OperatorToken(word)
            self.state = State.CONDITION_NAME
        elif self.state == State.CONDITION_NAME:
            yield ConditionNameToken(word)
            self.state = State.ARGUMENTS
        elif self.state == State.ARGUMENTS:
            yield ArgumentToken(word)


class TestParser2:
    # combine all args into a single arg; don't split at whitespace
    treat_args_as_single = ["dialog", "dialog_chain", "music_playing", "play_music"]

    def __init__(self, words):
        self.words = words
        self.state = None
        self.fsm = SimpleFSM((
            (None, "act", "actname", "act"),
            (None, "cdn", "cdnname", "cdn"),
            ("actname", "str", "str", "actname"),
            ("cndname", "str", "str", "eof"),
        ))

    def parse(self):
        for word in self.words:
            for token in self.parse_word(word):
                print("token::", token)
                yield token

    def as_string(self):
        tokens = list(self.parse())
        types = {type(i) for i in tokens}

        return " ".join(i.value for i in tokens)

        if ActionNameToken in types:
            if tokens[0].value in self.treat_args_as_single:
                return tokens[0].value, [" ".join([i.value for i in tokens[1:]])]
            return tokens[0].value, [i.value for i in tokens[1:]]
        if ConditionNameToken in types:
            if tokens[1].value in self.treat_args_as_single:
                return tokens[0].value, tokens[1].value, [" ".join([i.value for i in tokens[2:]])]
            return tokens[0].value, tokens[1].value, [i.value for i in tokens[2:]]
        raise ValueError

    def parse_word(self, token):
        token_class, word = token

        action = None
        if token_class == WRD:
            if word.startswith("act"):
                # name, prio = re.match(r"(\D+)\s*(\d+)", word).groups()
                # yield ActionNameToken(name)
                # yield PriorityToken(prio)
                action = self.fsm("act")
            elif word.startswith("cond"):
                # name, prio = re.match(r"(\D+)(\d+)", word).groups()
                # yield ConditionNameToken(name)
                # yield PriorityToken(prio)
                action = self.fsm("cnd")
            else:
                action = self.fsm("str")

        if "act" == action:
            pass
        if "actname" == action:
            yield ActionNameToken(word)
        if "cnd" == action:
            pass
        if "cndname" == action:
            yield ConditionNameToken(word)

        print(self.fsm.state, token, action)

        # elif self.state == State.ACTION:
        #     self.state = State.ARGUMENTS
        # elif self.state == State.CONDITION:
        #     yield OperatorToken(word)
        #     self.state = State.CONDITION_NAME
        # elif self.state == State.CONDITION_NAME:
        #     self.state = State.ARGUMENTS
        # elif self.state == State.ARGUMENTS:
        #     yield ArgumentToken(word)
