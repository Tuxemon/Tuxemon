# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import MagicMock, Mock

from tuxemon.states.combat.combat_ui import CombatUI


class TestCombatUI(unittest.TestCase):

    def test_init(self):
        combat_ui = CombatUI()
        self.assertEqual(combat_ui._hp_bars, {})
        self.assertEqual(combat_ui._exp_bars, {})

    def test_draw_hp_bars(self):
        combat_ui = CombatUI()
        graphics = Mock()
        graphics.hud.hp_bar_player = True
        graphics.hud.hp_bar_opponent = True
        hud = {
            Mock(player=True): Mock(image=Mock()),
            Mock(player=False): Mock(image=Mock()),
        }
        combat_ui._hp_bars = {monster: Mock() for monster in hud.keys()}
        combat_ui.create_rect_for_bar = MagicMock(return_value=Mock())
        combat_ui.draw_hp_bars(graphics, hud)
        for monster, sprite in hud.items():
            if sprite.player:
                combat_ui._hp_bars[monster].draw.assert_called_once_with(
                    sprite.image, combat_ui.create_rect_for_bar.return_value
                )
            else:
                combat_ui._hp_bars[monster].draw.assert_called_once_with(
                    sprite.image, combat_ui.create_rect_for_bar.return_value
                )

    def test_draw_hp_bars_no_player(self):
        combat_ui = CombatUI()
        graphics = Mock()
        graphics.hud.hp_bar_player = False
        graphics.hud.hp_bar_opponent = True
        hud = {
            Mock(player=True): Mock(image=Mock()),
            Mock(player=False): Mock(image=Mock()),
        }
        combat_ui._hp_bars = {monster: Mock() for monster in hud.keys()}
        combat_ui.create_rect_for_bar = MagicMock(return_value=Mock())
        combat_ui.draw_hp_bars(graphics, hud)
        for monster, sprite in hud.items():
            if sprite.player:
                self.assertFalse(combat_ui._hp_bars[monster].draw.called)
            else:
                combat_ui._hp_bars[monster].draw.assert_called_once_with(
                    sprite.image, combat_ui.create_rect_for_bar.return_value
                )

    def test_draw_exp_bars(self):
        combat_ui = CombatUI()
        graphics = Mock()
        graphics.hud.exp_bar_player = True
        hud = {
            Mock(player=True): Mock(image=Mock()),
            Mock(player=False): Mock(image=Mock()),
        }
        combat_ui._exp_bars = {monster: Mock() for monster in hud.keys()}
        combat_ui.create_rect_for_bar = MagicMock(return_value=Mock())
        combat_ui.draw_exp_bars(graphics, hud)
        for monster, sprite in hud.items():
            if sprite.player:
                combat_ui._exp_bars[monster].draw.assert_called_once_with(
                    sprite.image, combat_ui.create_rect_for_bar.return_value
                )
            else:
                self.assertFalse(combat_ui._exp_bars[monster].draw.called)

    def test_create_rect_for_bar(self):
        combat_ui = CombatUI()
        hud = Mock()
        hud.image.get_width.return_value = 100
        rect = combat_ui.create_rect_for_bar(hud, 70, 8, 0)
        self.assertEqual(rect.width, 350)
        self.assertEqual(rect.height, 40)
        self.assertEqual(rect.right, 60)
        self.assertEqual(rect.top, 0)

    def test_draw_all_ui(self):
        combat_ui = CombatUI()
        graphics = Mock()
        hud = {
            Mock(player=True): Mock(image=Mock()),
            Mock(player=False): Mock(image=Mock()),
        }
        combat_ui.draw_hp_bars = MagicMock()
        combat_ui.draw_exp_bars = MagicMock()
        combat_ui.draw_all_ui(graphics, hud)
        combat_ui.draw_hp_bars.assert_called_once_with(graphics, hud)
        combat_ui.draw_exp_bars.assert_called_once_with(graphics, hud)
