# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""
There are quite a few hacks in here to get this working for single player only
notably, the use of self.game
"""

from __future__ import annotations

import logging
from abc import ABC
from collections import defaultdict
from collections.abc import MutableMapping
from functools import partial
from typing import TYPE_CHECKING, Literal, Optional

import pygame
from pygame.rect import Rect

from tuxemon import audio, graphics, prepare, tools
from tuxemon.combat import fainted
from tuxemon.db import GenderType, SeenStatus
from tuxemon.locale import T
from tuxemon.menu.interface import ExpBar, HpBar
from tuxemon.menu.menu import Menu
from tuxemon.sprite import CaptureDeviceSprite, Sprite
from tuxemon.tools import scale, scale_sequence

if TYPE_CHECKING:
    from tuxemon.db import BattleGraphicsModel
    from tuxemon.item.item import Item
    from tuxemon.monster import Monster
    from tuxemon.npc import NPC

logger = logging.getLogger(__name__)

sprite_layer = 0
hud_layer = 100
TimedCallable = tuple[partial[None], float]


def toggle_visible(sprite: Sprite) -> None:
    sprite.visible = not sprite.visible


def scale_area(area: tuple[int, int, int, int]) -> Rect:
    return Rect(tools.scale_sequence(area))


class CombatAnimations(ABC, Menu[None]):
    """
    Collection of combat animations.

    Mixin-ish thing until things are sorted out.
    Mostly just a collections of methods to animate the sprites

    These methods should not, without [many] exception[s], manipulate
    game/combat state.  These should just move sprites around
    the screen, with the occasional creation/removal of sprites....
    but never game objects.
    """

    def __init__(
        self,
        players: tuple[NPC, NPC],
        graphics: BattleGraphicsModel,
    ) -> None:
        super().__init__()
        self.players = list(players)
        self.graphics = graphics

        self.monsters_in_play: MutableMapping[
            NPC, list[Monster]
        ] = defaultdict(list)
        self._monster_sprite_map: MutableMapping[Monster, Sprite] = {}
        self.hud: MutableMapping[Monster, Sprite] = {}
        self.is_trainer_battle = False
        self.capdevs: list[CaptureDeviceSprite] = []
        self.text_animations_queue: list[TimedCallable] = []
        self._text_animation_time_left: float = 0
        self._hp_bars: MutableMapping[Monster, HpBar] = {}
        self._exp_bars: MutableMapping[Monster, ExpBar] = {}
        self._status_icons: defaultdict[Monster, list[Sprite]] = defaultdict(
            list
        )

        player = prepare.PLAYER_COMBAT
        opponent = prepare.OPPONENT_COMBAT

        # convert the list/tuple of coordinates to Rects
        layout = [
            {
                key: list(map(scale_area, [(*value,)]))
                for key, value in p.items()
            }
            for p in (player, opponent)
        ]

        # end config =========================================

        # map positions to players
        self._layout = {
            player: layout[index] for index, player in enumerate(self.players)
        }

    def animate_open(self) -> None:
        self.transition_none_normal()

    def transition_none_normal(self) -> None:
        """From newly opened to normal."""
        self.animate_parties_in()

        for player, layout in self._layout.items():
            if not player.isplayer and player.max_position > 1:
                pass
            else:
                self.animate_party_hud_in(player, layout["party"][0])

        self.task(partial(self.animate_trainer_leave, self.players[0]), 3)

        if self.is_trainer_battle:
            self.task(partial(self.animate_trainer_leave, self.players[1]), 3)

    def blink(self, sprite: Sprite) -> None:
        self.task(partial(toggle_visible, sprite), 0.20, 8)

    def animate_trainer_leave(self, trainer: Monster) -> None:
        sprite = self._monster_sprite_map[trainer]
        if self.get_side(sprite.rect) == "left":
            x_diff = -scale(150)
        else:
            x_diff = scale(150)

        self.animate(sprite.rect, x=x_diff, relative=True, duration=0.8)

    def animate_monster_release(
        self,
        npc: NPC,
        monster: Monster,
        sprite: Sprite,
    ) -> None:
        feet_list = list(self._layout[npc]["home"][0].center)
        feet = (feet_list[0], feet_list[1] + tools.scale(11))

        capdev = self.load_sprite(f"gfx/items/{monster.capture_device}.png")
        graphics.scale_sprite(capdev, 0.4)
        capdev.rect.center = feet[0], feet[1] - scale(60)

        # animate the capdev falling
        fall_time = 0.7
        animate = partial(
            self.animate,
            duration=fall_time,
            transition="out_quad",
        )
        animate(capdev.rect, bottom=feet[1], transition="in_back")
        animate(capdev, rotation=720, initial=0)

        # animate the capdev fading away
        delay = fall_time + 0.6
        fade_duration = 0.9
        h = capdev.rect.height
        animate = partial(self.animate, duration=fade_duration, delay=delay)
        animate(capdev, width=1, height=h * 1.5)
        animate(capdev.rect, y=-scale(14), relative=True)

        # convert the capdev sprite so we can fade it easily
        def func() -> None:
            capdev.image = graphics.convert_alpha_to_colorkey(capdev.image)
            self.animate(
                capdev.image,
                set_alpha=0,
                initial=255,
                duration=fade_duration,
            )

        self.task(func, delay)
        self.task(capdev.kill, fall_time + delay + fade_duration)

        # load monster and set in final position
        monster_sprite = monster.get_sprite(
            "back" if npc == self.players[0] else "front",
            midbottom=feet,
        )
        self.sprites.add(monster_sprite)
        self._monster_sprite_map[monster] = monster_sprite

        # position monster_sprite off screen and set animation to move it
        # back to final spot
        monster_sprite.rect.top = self.client.screen.get_height()
        self.animate(
            monster_sprite.rect,
            bottom=feet[1],
            transition="out_back",
            duration=0.9,
            delay=fall_time + 0.5,
        )

        # capdev opening animation
        assert sprite.animation
        sprite.rect.midbottom = feet
        self.task(sprite.animation.play, 1.3)
        self.task(partial(self.sprites.add, sprite), 1.3)

        # attempt to load and queue up combat_call
        call_sound = audio.load_sound(monster.combat_call, None)
        if call_sound:
            self.task(call_sound.play, 1.3)

    def animate_sprite_spin(self, sprite: Sprite) -> None:
        self.animate(
            sprite,
            rotation=360,
            initial=0,
            duration=0.8,
            transition="in_out_quint",
        )

    def animate_sprite_tackle(self, sprite: Sprite) -> None:
        duration = 0.3
        original_x = sprite.rect.x

        if self.get_side(sprite.rect) == "left":
            delta = scale(14)
        else:
            delta = -scale(14)

        self.animate(
            sprite.rect,
            x=original_x + delta,
            duration=duration,
            transition="out_circ",
        )
        self.animate(
            sprite.rect,
            x=original_x,
            duration=duration,
            transition="in_out_circ",
            delay=0.35,
        )

    def animate_monster_faint(self, monster: Monster) -> None:
        # TODO: rename to distinguish fainting/leaving
        def kill() -> None:
            self._monster_sprite_map[monster].kill()
            self.hud[monster].kill()
            for sprite in self._status_icons[monster]:
                sprite.kill()
            self._status_icons[monster].clear()
            del self._monster_sprite_map[monster]
            del self.hud[monster]

        self.animate_monster_leave(monster)
        self.task(kill, 2)

        for monsters in self.monsters_in_play.values():
            try:
                monsters.remove(monster)
            except ValueError:
                pass

        # update tuxemon balls to reflect fainted tuxemon
        self.animate_update_party_hud()

    def animate_sprite_take_damage(self, sprite: Sprite) -> None:
        original_x, original_y = sprite.rect.topleft
        animate = partial(
            self.animate,
            sprite.rect,
            duration=1,
            transition="in_out_elastic",
        )
        ani = animate(x=original_x, initial=original_x + scale(400))
        # just want the end of the animation, not the entire thing
        ani._elapsed = 0.735
        ani = animate(y=original_y, initial=original_y - scale(400))
        # just want the end of the animation, not the entire thing
        ani._elapsed = 0.735

    def animate_hp(self, monster: Monster) -> None:
        value = monster.current_hp / monster.hp
        hp_bar = self._hp_bars[monster]
        self.animate(
            hp_bar,
            value=value,
            duration=0.7,
            transition="out_quint",
        )

    def build_animate_hp_bar(
        self,
        monster: Monster,
        initial: int = 0,
    ) -> None:
        self._hp_bars[monster] = HpBar(initial)
        self.animate_hp(monster)

    def animate_exp(self, monster: Monster) -> None:
        target_previous = monster.experience_required()
        target_next = monster.experience_required(1)
        value = max(
            0,
            min(
                1,
                (monster.total_experience - target_previous)
                / (target_next - target_previous),
            ),
        )
        exp_bar = self._exp_bars[monster]
        self.animate(
            exp_bar,
            value=value,
            duration=0.7,
            transition="out_quint",
        )

    def build_animate_exp_bar(
        self,
        monster: Monster,
        initial: int = 0,
    ) -> None:
        self._exp_bars[monster] = ExpBar(initial)
        self.animate_exp(monster)

    def build_hud_text(
        self, monster: Monster, source: bool
    ) -> pygame.surface.Surface:
        """
        Return the text image for use on the callout of the monster.

        Parameters:
            monster: The monster whose name and level will be printed.
            source: True (opponent), False (Player)

        Returns:
            Surface with the name and level of the monster written.

        """
        tuxepedia = self.players[0].tuxepedia
        icon: str = ""
        symbol: str = ""
        if monster.gender == GenderType.male:
            icon += "♂"
        if monster.gender == GenderType.female:
            icon += "♀"
        # shows captured symbol (wild encounter)
        if not self.is_trainer_battle and monster.slug in tuxepedia and source:
            if tuxepedia[monster.slug] == SeenStatus.caught:
                symbol += "◉"
        return self.shadow_text(
            f"{monster.name}{icon} Lv.{monster.level}{symbol}"
        )

    def get_side(self, rect: Rect) -> Literal["left", "right"]:
        """
        [WIP] get 'side' of screen rect is in.

        :type rect: Rect
        :return: basestring
        """
        return "left" if rect.centerx < scale(100) else "right"

    def animate_monster_leave(self, monster: Monster) -> None:
        sprite = self._monster_sprite_map[monster]
        if self.get_side(sprite.rect) == "left":
            x_diff = -scale(150)
        else:
            x_diff = scale(150)

        cry = (
            monster.combat_call
            if monster.current_hp > 0
            else monster.faint_call
        )
        sound = audio.load_sound(cry, None)
        sound.play()
        self.animate(sprite.rect, x=x_diff, relative=True, duration=2)
        for sprite in self._status_icons[monster]:
            self.animate(sprite.image, initial=255, set_alpha=0, duration=2)

    def build_hud(self, home: Rect, monster: Monster) -> None:
        def build_left_hud() -> Sprite:
            hud = self.load_sprite(
                self.graphics.hud.hud_opponent,
                layer=hud_layer,
            )
            text = self.build_hud_text(monster, True)
            hud.image.blit(text, scale_sequence((5, 5)))
            hud.rect.bottomright = 0, home.bottom
            hud.player = False
            animate(hud.rect, right=home.right)
            return hud

        def build_right_hud() -> Sprite:
            hud = self.load_sprite(
                self.graphics.hud.hud_player,
                layer=hud_layer,
            )
            text = self.build_hud_text(monster, False)
            hud.image.blit(text, scale_sequence((12, 11)))
            hud.rect.bottomleft = home.right, home.bottom
            hud.player = True
            animate(hud.rect, left=home.left)
            return hud

        animate = partial(
            self.animate,
            duration=2.0,
            delay=1.3,
        )
        if self.get_side(home) == "right":
            hud = build_right_hud()
        else:
            hud = build_left_hud()
        self.hud[monster] = hud

        self.build_animate_hp_bar(monster)
        if hud.player:
            self.build_animate_exp_bar(monster)

    def animate_party_hud_in(self, player: NPC, home: Rect) -> None:
        """
        Party HUD is the arrow thing with balls.  Yes, that one.

        Parameters:
            player: The player whose HUD is being animated.
            home: Location and size of the HUD.

        """
        if self.get_side(home) == "left":
            if self.is_trainer_battle:
                tray = self.load_sprite(
                    self.graphics.hud.tray_opponent,
                    bottom=home.bottom,
                    right=0,
                    layer=hud_layer,
                )
                self.animate(
                    tray.rect, right=home.right, duration=2, delay=1.5
                )
                centerx = home.right - scale(13)
                offset = scale(8)
            else:
                pass

        else:
            tray = self.load_sprite(
                self.graphics.hud.tray_player,
                bottom=home.bottom,
                left=home.right,
                layer=hud_layer,
            )
            self.animate(tray.rect, left=home.left, duration=2, delay=1.5)
            centerx = home.left + scale(13)
            offset = -scale(8)

        for index in range(player.party_limit):
            # opponent is wild monster = no tuxeballs
            if any(t for t in player.monsters if t.wild):
                continue
            status = None

            monster: Optional[Monster]
            # opponent tuxemon should order from left to right
            if self.get_side(home) == "left":
                pos = len(player.monsters) - index - 1
            else:
                pos = index
            if len(player.monsters) > index:
                monster = player.monsters[index]
                if fainted(monster):
                    status = "faint"
                    sprite = self.load_sprite(
                        self.graphics.icons.icon_faint,
                        top=tray.rect.top + scale(1),
                        centerx=centerx - pos * offset,
                        layer=hud_layer,
                    )
                elif len(monster.status) > 0:
                    status = "effected"
                    sprite = self.load_sprite(
                        self.graphics.icons.icon_status,
                        top=tray.rect.top + scale(1),
                        centerx=centerx - pos * offset,
                        layer=hud_layer,
                    )
                else:
                    status = "alive"
                    sprite = self.load_sprite(
                        self.graphics.icons.icon_alive,
                        top=tray.rect.top + scale(1),
                        centerx=centerx - pos * offset,
                        layer=hud_layer,
                    )
            else:
                status = "empty"
                monster = None
                sprite = self.load_sprite(
                    self.graphics.icons.icon_empty,
                    top=tray.rect.top + scale(1),
                    centerx=centerx - index * offset,
                    layer=hud_layer,
                )
            capdev = CaptureDeviceSprite(
                sprite=sprite,
                tray=tray,
                monster=monster,
                state=status,
                icon=self.graphics.icons,
            )
            self.capdevs.append(capdev)
            animate = partial(
                self.animate,
                duration=1.5,
                delay=2.2 + index * 0.2,
            )
            capdev.animate_capture(animate)

    def animate_update_party_hud(self) -> None:
        """
        Update the balls in the party HUD to reflect fainted Tuxemon.

        Note:
            Party HUD is the arrow thing with balls.  Yes, that one.

        """
        for dev in self.capdevs:
            prev = dev.state
            if prev != dev.update_state():
                animate = partial(self.animate, duration=0.1, delay=0.1)
                dev.animate_capture(animate)

    def animate_parties_in(self) -> None:
        surface = pygame.display.get_surface()
        x, y, w, h = surface.get_rect()

        # Get background image if passed in
        self.background = self.load_sprite(self.graphics.background)
        assert self.background

        player, opponent = self.players
        opp_mon = opponent.monsters[0]
        player_home = self._layout[player]["home"][0]
        opp_home = self._layout[opponent]["home"][0]
        y_mod = scale(50)
        duration = 3

        back_island = self.load_sprite(
            self.graphics.island_back,
            bottom=opp_home.bottom + y_mod,
            right=0,
        )

        # animation, begin battle
        if self.is_trainer_battle:
            combat_front = opponent.template[0].sprite_name
            enemy = self.load_sprite(
                f"gfx/sprites/player/{combat_front}.png",
                bottom=back_island.rect.bottom - scale(12),
                centerx=back_island.rect.centerx,
            )
            self._monster_sprite_map[opponent] = enemy
        else:
            enemy = opp_mon.get_sprite(
                "front",
                bottom=back_island.rect.bottom - scale(12),
                centerx=back_island.rect.centerx,
            )
            self._monster_sprite_map[opp_mon] = enemy
            self.monsters_in_play[opponent].append(opp_mon)
            self.build_hud(self._layout[opponent]["hud"][0], opp_mon)

        self.sprites.add(enemy)

        if self.is_trainer_battle:
            params = {"name": opponent.name.upper()}
            self.alert(T.format("combat_trainer_appeared", params))
        else:
            params = {"name": opp_mon.name.upper()}
            self.alert(T.format("combat_wild_appeared", params))

        front_island = self.load_sprite(
            self.graphics.island_front,
            bottom=player_home.bottom - y_mod,
            left=w,
        )

        combat_back = player.template[0].sprite_name
        player_back = self.load_sprite(
            f"gfx/sprites/player/{combat_back}_back.png",
            bottom=front_island.rect.centery + scale(6),
            centerx=front_island.rect.centerx,
        )
        assert player_back
        self._monster_sprite_map[player] = player_back

        def flip() -> None:
            enemy.image = pygame.transform.flip(enemy.image, True, False)
            player_back.image = pygame.transform.flip(
                player_back.image, True, False
            )

        flip()
        self.task(flip, 1.5)

        if not self.is_trainer_battle:
            self.task(audio.load_sound(opp_mon.combat_call, None).play, 1.5)

        animate = partial(
            self.animate, transition="out_quad", duration=duration
        )

        # top trainer
        animate(enemy.rect, back_island.rect, centerx=opp_home.centerx)
        animate(
            enemy.rect,
            back_island.rect,
            y=-y_mod,
            transition="out_back",
            relative=True,
        )

        # bottom trainer
        animate(
            player_back.rect, front_island.rect, centerx=player_home.centerx
        )
        animate(
            player_back.rect,
            front_island.rect,
            y=y_mod,
            transition="out_back",
            relative=True,
        )

    def animate_capture_monster(
        self,
        is_captured: bool,
        num_shakes: int,
        monster: Monster,
        item: Item,
        sprite: Sprite,
    ) -> None:
        """
        Animation for capturing monsters.

        Parameters:
            is_captured: Whether the monster will be captured.
            num_shakes: Number of shakes before animation ends.
            monster: The monster to capture.

        """
        monster_sprite = self._monster_sprite_map[monster]
        capdev = self.load_sprite(item.sprite)
        animate = partial(
            self.animate, capdev.rect, transition="in_quad", duration=1.0
        )
        graphics.scale_sprite(capdev, 0.4)
        capdev.rect.center = scale(0), scale(0)
        animate(x=monster_sprite.rect.centerx)
        animate(y=monster_sprite.rect.centery)
        self.task(partial(toggle_visible, monster_sprite), 1.0)

        def kill() -> None:
            self._monster_sprite_map[monster].kill()
            self.hud[monster].kill()
            del self._monster_sprite_map[monster]
            del self.hud[monster]

        # TODO: cache this sprite from the first time it's used.
        assert sprite.animation
        self.task(sprite.animation.play, 1.0)
        self.task(partial(self.sprites.add, sprite), 1.0)
        sprite.rect.midbottom = monster_sprite.rect.midbottom

        def shake_ball(initial_delay: float) -> None:
            animate = partial(
                self.animate,
                duration=0.1,
                transition="linear",
                delay=initial_delay,
            )
            animate(capdev.rect, y=scale(3), relative=True)

            animate = partial(
                self.animate,
                duration=0.2,
                transition="linear",
                delay=initial_delay + 0.1,
            )
            animate(capdev.rect, y=-scale(6), relative=True)

            animate = partial(
                self.animate,
                duration=0.1,
                transition="linear",
                delay=initial_delay + 0.3,
            )
            animate(capdev.rect, y=scale(3), relative=True)

        for i in range(0, num_shakes):
            # leave a 0.6s wait between each shake
            shake_ball(1.8 + i * 1.0)

        combat = item.combat_state
        if is_captured and combat:
            combat._captured_mon = monster
            self.task(kill, 2 + num_shakes)
            action_time = num_shakes + 1.8
            # Tuxepedia: set monster as caught (2)
            if self.players[0].tuxepedia[monster.slug] == SeenStatus.seen:
                combat._new_tuxepedia = True
            self.players[0].tuxepedia[monster.slug] = SeenStatus.caught
            # Display 'Gotcha!' first.
            self.task(combat.end_combat, action_time + 4)
            gotcha = T.translate("gotcha")
            info = None
            # if party
            params = {"name": monster.name.upper()}
            if len(self.players[0].monsters) >= self.players[0].party_limit:
                info = T.format("gotcha_kennel", params)
            else:
                info = T.format("gotcha_team", params)
            if info:
                gotcha += "\n" + info
                action_time += len(gotcha) * prepare.LETTER_TIME
            self.task(
                partial(self.alert, gotcha),
                action_time,
            )
        else:
            breakout_delay = 1.8 + num_shakes * 1.0
            self.task(  # make the monster appear again!
                partial(toggle_visible, monster_sprite),
                breakout_delay,
            )
            self.task(
                audio.load_sound(monster.combat_call, None).play,
                breakout_delay,
            )
            self.task(sprite.animation.play, breakout_delay)
            self.task(capdev.kill, breakout_delay)
            self.task(
                partial(self.blink, sprite),
                breakout_delay + 0.5,
            )
            label = f"captured_failed_{num_shakes}"
            failed = T.translate(label)
            breakout_delay += len(failed) * prepare.LETTER_TIME
            self.task(
                partial(self.alert, failed),
                breakout_delay,
            )
