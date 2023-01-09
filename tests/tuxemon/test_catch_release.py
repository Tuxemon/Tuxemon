# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest import mock

from tuxemon.monster import Monster
from tuxemon.npc import NPC


def mockNPC(self) -> None:

    self.monsters = []
    self.isplayer = True
    self.game_variables = {}
    self.monster_boxes = {}
    self.monster_boxes["Kennel"] = []


class TestCatchTuxemon(unittest.TestCase):

    # Can't release Tuxemon if it is the only one in the party.
    def test_release_one(self):
        with mock.patch.object(NPC, "__init__", mockNPC):
            npc = NPC()
            self.assertEqual(len(npc.monsters), 0)
            self.assertEqual(len(npc.monster_boxes["Kennel"]), 0)

            monster = Monster()
            npc.add_monster(monster)
            self.assertEqual(len(npc.monsters), 1)
            npc.release_monster(monster)
            self.assertEqual(len(npc.monsters), 1)

    # Tuxemon can be released if there is another in the party
    def test_release_two(self):
        with mock.patch.object(NPC, "__init__", mockNPC):
            npc = NPC()
            monsterA = Monster()
            npc.add_monster(monsterA)
            self.assertEqual(len(npc.monsters), 1)

            monsterB = Monster()
            npc.add_monster(monsterB)
            self.assertEqual(len(npc.monsters), 2)

            npc.release_monster(monsterA)
            self.assertEqual(len(npc.monsters), 1)

            self.assertEqual(npc.monsters[0], monsterB)
            self.assertNotEqual(npc.monsters[0], monsterA)

    # Can't have more than 6 Tuxemon in party. The excess goes into the Kennel.
    def test_catch_multiple(self):
        with mock.patch.object(NPC, "__init__", mockNPC):
            npc = NPC()
            self.assertEqual(len(npc.monsters), 0)

            monsterA = Monster()
            npc.add_monster(monsterA)

            monsterB = Monster()
            npc.add_monster(monsterB)

            monsterC = Monster()
            npc.add_monster(monsterC)

            monsterD = Monster()
            npc.add_monster(monsterD)

            monsterE = Monster()
            npc.add_monster(monsterE)
            self.assertEqual(len(npc.monsters), 5)

            monsterF = Monster()
            npc.add_monster(monsterF)
            self.assertEqual(len(npc.monsters), 6)
            self.assertEqual(len(npc.monster_boxes["Kennel"]), 0)

            monsterG = Monster()
            npc.add_monster(monsterG)
            self.assertEqual(len(npc.monsters), 6)
            self.assertEqual(len(npc.monster_boxes["Kennel"]), 1)
