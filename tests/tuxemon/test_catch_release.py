# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest import mock

from tuxemon.monster import Monster
from tuxemon.npc import NPC
from tuxemon.prepare import KENNEL, PARTY_LIMIT


def mockNPC(self) -> None:
    self.monsters = []
    self.isplayer = True
    self.game_variables = {}
    self.monster_boxes = {}
    self.monster_boxes[KENNEL] = []


class TestCatchTuxemon(unittest.TestCase):
    # Can't release Tuxemon if it is the only one in the party.
    def setUp(self):
        with mock.patch.object(NPC, "__init__", mockNPC):
            self.npc = NPC()

    def test_release_one(self):
        self.assertEqual(len(self.npc.monsters), 0)
        self.assertEqual(len(self.npc.monster_boxes[KENNEL]), 0)

        monster = Monster()
        self.npc.add_monster(monster, len(self.npc.monsters))
        self.assertEqual(len(self.npc.monsters), 1)
        self.npc.release_monster(monster)
        self.assertEqual(len(self.npc.monsters), 1)

    # Tuxemon can be released if there is another in the party
    def test_release_two(self):
        monsterA = Monster()
        self.npc.add_monster(monsterA, len(self.npc.monsters))
        self.assertEqual(len(self.npc.monsters), 1)

        monsterB = Monster()
        self.npc.add_monster(monsterB, len(self.npc.monsters))
        self.assertEqual(len(self.npc.monsters), 2)

        self.npc.release_monster(monsterA)
        self.assertEqual(len(self.npc.monsters), 1)

        self.assertEqual(self.npc.monsters[0], monsterB)
        self.assertNotEqual(self.npc.monsters[0], monsterA)

    # Can't have more than 6 Tuxemon in party. The excess goes into the Kennel.
    def test_catch_multiple(self):
        self.assertEqual(len(self.npc.monsters), 0)

        monsterA = Monster()
        self.npc.add_monster(monsterA, len(self.npc.monsters))

        monsterB = Monster()
        self.npc.add_monster(monsterB, len(self.npc.monsters))

        monsterC = Monster()
        self.npc.add_monster(monsterC, len(self.npc.monsters))

        monsterD = Monster()
        self.npc.add_monster(monsterD, len(self.npc.monsters))

        monsterE = Monster()
        self.npc.add_monster(monsterE, len(self.npc.monsters))
        self.assertEqual(len(self.npc.monsters), 5)

        monsterF = Monster()
        self.npc.add_monster(monsterF, len(self.npc.monsters))
        self.assertEqual(len(self.npc.monsters), PARTY_LIMIT)
        self.assertEqual(len(self.npc.monster_boxes[KENNEL]), 0)

        monsterG = Monster()
        self.npc.add_monster(monsterG, len(self.npc.monsters))
        self.assertEqual(len(self.npc.monsters), PARTY_LIMIT)
        self.assertEqual(len(self.npc.monster_boxes[KENNEL]), 1)
