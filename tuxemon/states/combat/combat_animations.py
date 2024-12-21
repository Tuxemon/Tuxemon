# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
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

from tuxemon import graphics, prepare, tools
from tuxemon.combat import alive_party, build_hud_text, fainted
from tuxemon.locale import T
from tuxemon.menu.interface import ExpBar, HpBar
from tuxemon.menu.menu import Menu
from tuxemon.sprite import CaptureDeviceSprite, Sprite
from tuxemon.tools import scale, scale_sequence

if TYPE_CHECKING:
    from tuxemon.animation import Animation
    from tuxemon.db import BattleGraphicsModel
    from tuxemon.item.item import Item
    from tuxemon.monster import Monster
    from tuxemon.npc import NPC

logger = logging.getLogger(__name__)

sprite_layer = 0
hud_layer = 100
TimedCallable = tuple[partial[None], float]


def toggle_visible(sprite: Sprite) -> None:
    sprite.toggle_visible()


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

        self.monsters_in_play: defaultdict[NPC, list[Monster]] = defaultdict(
            list
        )
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

        _right = prepare.RIGHT_COMBAT
        _left = prepare.LEFT_COMBAT

        # convert the list/tuple of coordinates to Rects
        layout = [
            {
                key: list(map(scale_area, [(*value,)]))
                for key, value in p.items()
            }
            for p in (_right, _left)
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
            self.animate_party_hud_in(player, layout["party"][0])

        for player in self.players[: 2 if self.is_trainer_battle else 1]:
            self.task(partial(self.animate_trainer_leave, player), 3)

    def blink(self, sprite: Sprite) -> None:
        self.task(partial(toggle_visible, sprite), 0.20, 8)

    def animate_trainer_leave(self, trainer: Monster) -> None:
        """Animate the trainer leaving the screen."""
        sprite = self._monster_sprite_map[trainer]
        side = self.get_side(sprite.rect)
        x_diff = scale(-150 if side == "left" else 150)
        self.animate(sprite.rect, x=x_diff, relative=True, duration=0.8)

    def animate_monster_release(
        self,
        npc: NPC,
        monster: Monster,
        sprite: Sprite,
    ) -> None:
        # Calculate feet position
        if npc.max_position > 1 and monster in self.monsters_in_play[npc]:
            monster_index = str(self.monsters_in_play[npc].index(monster))
        else:
            monster_index = ""

        feet = (
            self._layout[npc][f"home{monster_index}"][0].center[0],
            self._layout[npc][f"home{monster_index}"][0].center[1]
            + tools.scale(11),
        )

        # Load and scale capture device sprite
        capdev = self.load_sprite(f"gfx/items/{monster.capture_device}.png")
        graphics.scale_sprite(capdev, 0.4)
        capdev.rect.center = (feet[0], feet[1] - tools.scale(60))

        # Animate capture device falling
        fall_time = 0.7
        animate_fall = partial(
            self.animate,
            duration=fall_time,
            transition="out_quad",
        )
        animate_fall(capdev.rect, bottom=feet[1], transition="in_back")
        animate_fall(capdev, rotation=720, initial=0)

        # Animate capture device fading away
        delay = fall_time + 0.6
        fade_duration = 0.9
        h = capdev.rect.height
        animate_fade = partial(
            self.animate, duration=fade_duration, delay=delay
        )
        animate_fade(capdev, width=1, height=h * 1.5)
        animate_fade(capdev.rect, y=-tools.scale(14), relative=True)

        # Convert capture device sprite for easy fading
        def convert_sprite() -> None:
            capdev.image = graphics.convert_alpha_to_colorkey(capdev.image)
            self.animate(
                capdev.image,
                set_alpha=0,
                initial=255,
                duration=fade_duration,
            )

        self.task(convert_sprite, delay)
        self.task(capdev.kill, fall_time + delay + fade_duration)

        # Load monster sprite and set final position
        monster_sprite = monster.get_sprite(
            "back" if npc == self.players[0] else "front",
            midbottom=feet,
        )
        self.sprites.add(monster_sprite)
        self._monster_sprite_map[monster] = monster_sprite

        # Position monster sprite off screen and animate it to final spot
        monster_sprite.rect.top = self.client.screen.get_height()
        self.animate(
            monster_sprite.rect,
            bottom=feet[1],
            transition="out_quad",
            duration=0.9,
            delay=fall_time + 0.5,
        )

        # Play capture device opening animation
        assert sprite.animation
        sprite.rect.midbottom = feet
        self.task(sprite.animation.play, 1.3)
        self.task(partial(self.sprites.add, sprite), 1.3)

        # Load and play combat call sound
        self.play_sound_effect(monster.combat_call, 1.3)

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
        """Animate a monster fainting and remove it."""

        def kill_monster() -> None:
            """Remove the monster's sprite and HUD elements."""
            self._monster_sprite_map[monster].kill()
            for icon in self._status_icons[monster]:
                icon.kill()
            self._status_icons[monster].clear()
            del self._monster_sprite_map[monster]
            self.delete_hud(monster)

        self.animate_monster_leave(monster)
        self.task(kill_monster, 2)

        for monsters in self.monsters_in_play.values():
            if monster in monsters:
                monsters.remove(monster)

        # Update the party HUD to reflect the fainted tuxemon
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
        diff_value = monster.total_experience - target_previous
        diff_target = target_next - target_previous
        value = max(0, min(1, (diff_value) / (diff_target)))
        if monster.levelling_up:
            value = 1.0
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

    def get_side(self, rect: Rect) -> Literal["left", "right"]:
        """
        Determine the side of the screen where the rectangle is located and
        return the side of the screen where the rectangle is located ("left"
        or "right")

        Parameters:
            rect: The rectangle to check.
        """
        return "left" if rect.centerx < scale(100) else "right"

    def animate_monster_leave(self, monster: Monster) -> None:
        sprite = self._monster_sprite_map[monster]
        x_diff = (
            -scale(150) if self.get_side(sprite.rect) == "left" else scale(150)
        )

        cry = (
            monster.combat_call
            if monster.current_hp > 0
            else monster.faint_call
        )
        self.play_sound_effect(cry)
        self.animate(sprite.rect, x=x_diff, relative=True, duration=2)
        for icon in self._status_icons[monster]:
            self.animate(icon.image, initial=255, set_alpha=0, duration=2)

    def check_hud(self, monster: Monster, filename: str) -> Sprite:
        """
        Checks whether exists or not a hud, it returns a sprite.
        To avoid building over an existing one.

        Parameters:
            monster: Monster who needs to update the hud.
            filename: Filename of the hud.

        """
        if monster in self.hud:
            return self.hud[monster]
        else:
            return self.load_sprite(filename, layer=hud_layer)

    def split_label(self, hud: Sprite, label: str, is_right: bool) -> None:
        """
        Checks whether exists a new line inside the label or not.
        If a new line exists, then it splits it.

        Parameters:
            hud: Hud's sprite.
            home: Label blit over the sprite.
            is_right: Boolean side (true: right side, false: left side).
                right side (player), left side (opponent)

        """
        if is_right:
            line1, line2 = prepare.HUD_RT_LINE1, prepare.HUD_RT_LINE2
        else:
            line1, line2 = prepare.HUD_LT_LINE1, prepare.HUD_LT_LINE2

        labels = label.splitlines()
        if len(labels) > 1:
            hud.image.blit(self.shadow_text(labels[0]), scale_sequence(line1))
            hud.image.blit(self.shadow_text(labels[1]), scale_sequence(line2))
        else:
            hud.image.blit(self.shadow_text(labels[0]), scale_sequence(line1))

    def build_hud(
        self, monster: Monster, hud_position: str, animate: bool = True
    ) -> None:
        """
        Builds the HUD for a monster.

        Parameters:
            monster: The monster that needs to update the HUD.
            hud_position: The part of the layout where the HUD will be displayed (e.g. "hud0", etc.).
            animate: Whether the HUD should be animated (slide in) or not.

        """
        trainer_battle = self.is_trainer_battle
        menu = self.graphics.menu
        assert monster.owner
        hud_rect = self._layout[monster.owner][hud_position][0]

        def build_hud_sprite(hud: Sprite, is_player: bool) -> Sprite:
            """
            Builds a HUD sprite for a monster.

            Parameters:
                hud: The HUD sprite to build.
                is_player: Whether the HUD is for the player or not.

            Returns:
                The built HUD sprite.
            """
            symbol = (
                self.players[0].tuxepedia.get(monster.slug)
                if not is_player
                else None
            )
            label = build_hud_text(
                menu, monster, is_player, trainer_battle, symbol
            )
            self.split_label(hud, label, is_player)
            if is_player:
                hud.rect.bottomleft = hud_rect.right, hud_rect.bottom
                hud.player = True
                if animate:
                    animate_func(hud.rect, left=hud_rect.left)
                else:
                    hud.rect.left = hud_rect.left
            else:
                hud.rect.bottomright = 0, hud_rect.bottom
                hud.player = False
                if animate:
                    animate_func(hud.rect, right=hud_rect.right)
                else:
                    hud.rect.right = hud_rect.right
            return hud

        if animate:
            animate_func = partial(self.animate, duration=2.0, delay=1.3)

        if self.get_side(hud_rect) == "right":
            hud = build_hud_sprite(
                self.check_hud(monster, self.graphics.hud.hud_player), True
            )
        else:
            hud = build_hud_sprite(
                self.check_hud(monster, self.graphics.hud.hud_opponent), False
            )

        self.hud[monster] = hud

        if animate:
            self.build_animate_hp_bar(monster)
            if hud.player:
                self.build_animate_exp_bar(monster)

    def _load_sprite(
        self, sprite_type: str, position: dict[str, int]
    ) -> Sprite:
        return self.load_sprite(sprite_type, **position)

    def animate_party_hud_left(
        self, home: Rect
    ) -> tuple[Optional[Sprite], int, int]:
        if self.is_trainer_battle:
            tray = self._load_sprite(
                self.graphics.hud.tray_opponent,
                {"bottom": home.bottom, "right": 0, "layer": hud_layer},
            )
            self.animate(tray.rect, right=home.right, duration=2, delay=1.5)
        else:
            tray = None
        centerx = home.right - scale(13)
        offset = scale(8)
        return tray, centerx, offset

    def animate_party_hud_right(self, home: Rect) -> tuple[Sprite, int, int]:
        tray = self._load_sprite(
            self.graphics.hud.tray_player,
            {"bottom": home.bottom, "left": home.right, "layer": hud_layer},
        )
        self.animate(tray.rect, left=home.left, duration=2, delay=1.5)
        centerx = home.left + scale(13)
        offset = -scale(8)
        return tray, centerx, offset

    def animate_party_hud_in(self, player: NPC, home: Rect) -> None:
        """
        Party HUD is the arrow thing with balls.  Yes, that one.

        Parameters:
            player: The player whose HUD is being animated.
            home: Location and size of the HUD.

        """
        if self.get_side(home) == "left":
            tray, centerx, offset = self.animate_party_hud_left(home)
        else:
            tray, centerx, offset = self.animate_party_hud_right(home)

        # If the tray is None (wild monster)
        if tray is None:
            return

        for index in range(player.party_limit):
            # Skip if the opponent is a wild monster (no tuxeballs)
            if any(t for t in player.monsters if t.wild):
                continue
            status = None

            monster: Optional[Monster]
            # Determine the position of the monster in the party
            if self.get_side(home) == "left":
                pos = len(player.monsters) - index - 1
            else:
                pos = index
            if len(player.monsters) > index:
                monster = player.monsters[index]
                if fainted(monster):
                    status = "faint"
                    sprite = self._load_sprite(
                        self.graphics.icons.icon_faint,
                        {
                            "top": tray.rect.top + scale(1),
                            "centerx": centerx - pos * offset,
                            "layer": hud_layer,
                        },
                    )
                elif len(monster.status) > 0:
                    status = "effected"
                    sprite = self._load_sprite(
                        self.graphics.icons.icon_status,
                        {
                            "top": tray.rect.top + scale(1),
                            "centerx": centerx - pos * offset,
                            "layer": hud_layer,
                        },
                    )
                else:
                    status = "alive"
                    sprite = self._load_sprite(
                        self.graphics.icons.icon_alive,
                        {
                            "top": tray.rect.top + scale(1),
                            "centerx": centerx - pos * offset,
                            "layer": hud_layer,
                        },
                    )
            else:
                status = "empty"
                monster = None
                sprite = self._load_sprite(
                    self.graphics.icons.icon_empty,
                    {
                        "top": tray.rect.top + scale(1),
                        "centerx": centerx - index * offset,
                        "layer": hud_layer,
                    },
                )

            # Create a CaptureDeviceSprite object
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
        """Animate the parties entering the battle scene."""
        x, y, w, h = prepare.SCREEN_RECT

        # Load background image
        self.background = self.load_sprite(self.graphics.background)
        assert self.background

        # Get player and opponent
        player, opponent = self.players
        opp_mon = opponent.monsters[0]
        player_home = self._layout[player]["home"][0]
        opp_home = self._layout[opponent]["home"][0]

        # Define animation constants
        y_mod = scale(50)

        # Load island backgrounds
        back_island = self.load_sprite(
            self.graphics.island_back,
            bottom=opp_home.bottom + y_mod,
            right=0,
        )
        front_island = self.load_sprite(
            self.graphics.island_front,
            bottom=player_home.bottom - y_mod,
            left=w,
        )

        # Load and animate opponent
        if self.is_trainer_battle:
            combat_front = opponent.template.combat_front
            enemy = self.load_sprite(
                f"gfx/sprites/player/{combat_front}.png",
                bottom=back_island.rect.bottom - scale(12),
                centerx=back_island.rect.centerx,
            )
            self._monster_sprite_map[opponent] = enemy
        else:
            enemy = opp_mon.get_sprite(
                "front",
                bottom=back_island.rect.bottom - scale(24),
                centerx=back_island.rect.centerx,
            )
            self._monster_sprite_map[opp_mon] = enemy
            self.monsters_in_play[opponent].append(opp_mon)
            self.update_hud(opponent)

        self.sprites.add(enemy)

        # Load and animate player
        combat_back = player.template.combat_front
        filename = f"gfx/sprites/player/{combat_back}_back.png"
        try:
            player_back = self.load_sprite(
                filename,
                bottom=front_island.rect.centery + scale(6),
                centerx=front_island.rect.centerx,
            )
        except:
            logger.warning(f"(File) {filename} cannot be found.")
            player_back = self.load_sprite(
                f"gfx/sprites/player/{combat_back}.png",
                bottom=front_island.rect.centery + scale(6),
                centerx=front_island.rect.centerx,
            )

        self._monster_sprite_map[player] = player_back
        self.flip_sprites(enemy, player_back)
        self.animate_sprites(enemy, back_island, front_island, player_back)
        if not self.is_trainer_battle:
            sound = self.players[1].monsters[0].combat_call
            self.play_sound_effect(sound, 1.5)
        self.display_alert_message()

    def flip_sprites(self, enemy: Sprite, player_back: Sprite) -> None:
        """Flip the sprites horizontally."""

        def flip() -> None:
            enemy.image = pygame.transform.flip(enemy.image, True, False)
            player_back.image = pygame.transform.flip(
                player_back.image, True, False
            )

        flip()
        self.task(flip, 1.5)

    def animate_sprites(
        self,
        enemy: Sprite,
        back_island: Sprite,
        front_island: Sprite,
        player_back: Sprite,
    ) -> None:
        """Animate the sprites."""
        y_mod = scale(50)
        duration = 3
        animate = partial(
            self.animate, transition="out_quad", duration=duration
        )

        animate(
            enemy.rect,
            back_island.rect,
            centerx=self._layout[self.players[1]]["home"][0].centerx,
        )
        animate(
            enemy.rect,
            back_island.rect,
            y=-y_mod,
            transition="out_back",
            relative=True,
        )
        animate(
            player_back.rect,
            front_island.rect,
            centerx=self._layout[self.players[0]]["home"][0].centerx,
        )
        animate(
            player_back.rect,
            front_island.rect,
            y=y_mod,
            transition="out_back",
            relative=True,
        )

    def play_sound_effect(
        self, sound: str, value: float = prepare.SOUND_VOLUME
    ) -> None:
        """Play the sound effect."""
        self.client.sound_manager.play_sound(sound, value)

    def display_alert_message(self) -> None:
        """Display the alert message."""
        if self.is_trainer_battle:
            params = {"name": self.players[1].name.upper()}
            self.alert(T.format("combat_trainer_appeared", params))
        else:
            params = {"name": self.players[1].monsters[0].name.upper()}
            self.alert(T.format("combat_wild_appeared", params))

    def animate_throwing(
        self,
        monster: Monster,
        item: Item,
    ) -> Sprite:
        """
        Animation for throwing the item.

        Parameters:
            monster: The monster being targeted.
            item: The item thrown at the monster.

        Returns:
            The animated item sprite.

        """
        monster_sprite = self._monster_sprite_map[monster]
        sprite = self.load_sprite(item.sprite)
        animate = partial(
            self.animate, sprite.rect, transition="in_quad", duration=1.0
        )
        graphics.scale_sprite(sprite, 0.4)
        sprite.rect.center = scale(0), scale(0)
        animate(x=monster_sprite.rect.centerx)
        animate(y=monster_sprite.rect.centery)
        return sprite

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
            is_captured: Whether the monster will be successfully captured.
            num_shakes: The number of times the capture device will shake.
            monster: The monster being captured.
            item: The capture device used to capture the monster.
            sprite: The sprite to animate.

        """
        monster_sprite = self._monster_sprite_map[monster]
        capdev = self.animate_throwing(monster, item)
        animate = partial(
            self.animate, capdev.rect, transition="in_quad", duration=1.0
        )
        self.task(partial(toggle_visible, monster_sprite), 1.0)

        # TODO: cache this sprite from the first time it's used.
        assert sprite.animation
        self.task(sprite.animation.play, 1.0)
        self.task(partial(self.sprites.add, sprite), 1.0)
        sprite.rect.midbottom = monster_sprite.rect.midbottom

        def kill_monster() -> None:
            self._monster_sprite_map[monster].kill()
            del self._monster_sprite_map[monster]
            self.delete_hud(monster)

        def shake_ball(initial_delay: float) -> None:
            # Define reusable shake animation functions
            def shake_up() -> Animation:
                return animate(
                    capdev.rect, y=scale(3), relative=True, duration=0.1
                )

            def shake_down() -> Animation:
                return animate(
                    capdev.rect, y=-scale(6), relative=True, duration=0.2
                )

            # Chain shake animations with delays
            self.task(shake_up, initial_delay)
            self.task(shake_down, initial_delay + 0.1)
            self.task(shake_up, initial_delay + 0.3)

        # Perform shakes with delays
        for i in range(num_shakes):
            shake_ball(1.8 + i * 1.0)

        combat = item.combat_state
        if is_captured and combat and monster.owner:
            trainer = monster.owner
            combat._captured_mon = monster

            def show_success(delay: float) -> None:
                self.task(combat.end_combat, delay + 4)
                gotcha = T.translate("gotcha")
                params = {"name": monster.name.upper()}
                if len(trainer.monsters) >= trainer.party_limit:
                    info = T.format("gotcha_kennel", params)
                else:
                    info = T.format("gotcha_team", params)
                gotcha += "\n" + info
                delay += len(gotcha) * prepare.LETTER_TIME
                self.task(
                    partial(self.alert, gotcha),
                    delay,
                )

            self.task(kill_monster, 2 + num_shakes)
            delay = num_shakes / 2
            self.task(partial(show_success, delay), num_shakes)
        else:
            breakout_delay = 1.8 + num_shakes * 1.0

            def show_monster(delay: float) -> None:
                self.task(partial(toggle_visible, monster_sprite), delay)
                self.play_sound_effect(monster.combat_call, delay)

            def capture_capsule(delay: float) -> None:
                assert sprite.animation
                self.task(sprite.animation.play, delay)
                self.task(capdev.kill, delay)

            def blink_monster(delay: float) -> None:
                self.task(partial(self.blink, sprite), delay + 0.5)

            def show_failure(delay: float) -> None:
                label = f"captured_failed_{num_shakes}"
                failed = T.translate(label)
                delay += len(failed) * prepare.LETTER_TIME
                self.task(
                    partial(self.alert, failed),
                    delay,
                )

            show_monster(breakout_delay)
            capture_capsule(breakout_delay)
            blink_monster(breakout_delay)
            show_failure(breakout_delay)

    def delete_hud(self, monster: Monster) -> None:
        """
        Removes the specified monster's entry from the HUD.

        Parameters:
            monster: The monster to remove from the HUD.
        """
        if monster in self.hud:
            self.hud[monster].kill()
            del self.hud[monster]

    def update_hud(self, character: NPC, animate: bool = True) -> None:
        """
        Updates hud (where it appears name, level, etc.).

        Parameters:
            character: The character whose HUD needs to be updated.
            animate: Whether to animate the HUD update. Defaults to True.

        """
        monsters = self.monsters_in_play.get(character)
        if not monsters:
            return

        alive_members = alive_party(character)
        if len(monsters) > 1 and len(monsters) <= len(alive_members):
            for i, monster in enumerate(monsters):
                self.build_hud(monster, f"hud{i}", animate)
        else:
            self.build_hud(monsters[0], "hud", animate)
