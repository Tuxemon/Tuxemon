# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""
There are quite a few hacks in here to get this working for single player only
notably, the use of self.game
"""

from __future__ import annotations

from abc import ABC
from collections import defaultdict
from collections.abc import Callable, MutableMapping
from functools import partial
from typing import TYPE_CHECKING, Literal

import pygame
from pygame.rect import Rect
from pygame.surface import Surface

from tuxemon import audio, graphics, tools
from tuxemon.db import GenderType, SeenStatus
from tuxemon.locale import T
from tuxemon.menu.interface import HpBar
from tuxemon.menu.menu import Menu
from tuxemon.sprite import Sprite
from tuxemon.tools import scale, scale_sequence

if TYPE_CHECKING:
    from tuxemon.db import BattleGraphicsModel
    from tuxemon.item.item import Item
    from tuxemon.monster import Monster
    from tuxemon.npc import NPC
    from tuxemon.states.park.park import ParkState

sprite_layer = 0
hud_layer = 100
TimedCallable = tuple[Callable[[], None], float]


def toggle_visible(sprite: Sprite) -> None:
    sprite.visible = not sprite.visible


def scale_area(area: tuple[int, int, int, int]) -> Rect:
    return Rect(tools.scale_sequence(area))


class ParkAnimations(ABC, Menu[None]):
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
        self.text_animations_queue: list[TimedCallable] = []
        self._text_animation_time_left: float = 0
        self._hp_bars: MutableMapping[Monster, HpBar] = {}

        # eventually store in a config somewhere
        # is a tuple because more areas is needed for multi monster, etc
        player = dict()
        player["home"] = ((0, 62, 95, 70),)
        player["hud"] = ((151, 57, 110, 50),)

        opponent = dict()
        opponent["home"] = ((140, 10, 95, 70),)
        opponent["hud"] = ((18, 0, 85, 30),)

        # convert the list/tuple of coordinates to Rects
        layout = [
            {key: list(map(scale_area, value)) for key, value in p.items()}
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
        self.task(partial(self.animate_trainer_leave, self.players[0]), 3)

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
    ) -> None:
        feet_list = list(self._layout[npc]["home"][0].center)
        feet = (feet_list[0], feet_list[1] + tools.scale(11))

        # load monster and set in final position
        monster_sprite = None
        if npc.isplayer:
            monster_sprite = self.load_sprite(
                f"gfx/sprites/player/{npc.template[0].combat_front}_small_back.png",
                midbottom=feet,
            )
        else:
            monster_sprite = monster.get_sprite(
                "front",
                midbottom=feet,
            )
        if monster_sprite:
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
            delay=0.7 + 0.5,
        )

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

    def build_animate_hp_bar(
        self,
        monster: Monster,
    ) -> None:
        self._hp_bars[monster] = HpBar(1)

    def build_text_left(self, monster: Monster) -> Surface:
        """
        Return the text image for use on the callout of the monster.

        Parameters:
            monster: The monster whose name and level will be printed.

        Returns:
            Surface with the name and level of the monster written.

        """
        player = self.players[0]
        tuxepedia = player.tuxepedia
        icon: str = ""
        symbol: str = ""
        if monster.gender == GenderType.male:
            icon += "♂"
        if monster.gender == GenderType.female:
            icon += "♀"
        # shows captured symbol (wild encounter)
        if monster.slug in tuxepedia:
            if tuxepedia[monster.slug] == SeenStatus.caught:
                symbol += "◉"
        text = f"{monster.name}{icon} Lv.{monster.level}{symbol}"
        return self.shadow_text(text)

    def build_text_right(self) -> tuple[Surface, Surface]:
        """
        Return the text image for use on the callout of the monster.

        Parameters:
            monster: The monster whose name and level will be printed.

        Returns:
            Surface with the name and level of the monster written.

        """
        player = self.players[0]
        encountered = T.format("menu_park_encountered")
        nr_enc = player.game_variables["menu_park_encountered"]
        captured = T.format("menu_park_captured")
        nr_cap = player.game_variables["menu_park_captured"]
        enc = f"{encountered}: {nr_enc}"
        cap = f"{captured}: {nr_cap}"

        return self.shadow_text(enc), self.shadow_text(cap)

    def get_side(self, rect: Rect) -> Literal["left", "right"]:
        """
        [WIP] get 'side' of screen rect is in.

        :type rect: Rect
        :return: basestring
        """
        return "left" if rect.centerx < scale(100) else "right"

    def build_hud(self, home: Rect, monster: Monster) -> None:
        def build_left_hud() -> Sprite:
            hud = self.load_sprite(
                "gfx/ui/combat/park_hp_opponent.png",
                layer=hud_layer,
            )
            text = self.build_text_left(monster)
            hud.image.blit(text, scale_sequence((5, 5)))
            hud.rect.bottomright = 0, home.bottom
            hud.player = False
            animate(hud.rect, right=home.right)
            return hud

        def build_right_hud() -> Sprite:
            hud = self.load_sprite(
                "gfx/ui/combat/park_hp_player.png",
                layer=hud_layer,
            )
            enc, cap = self.build_text_right()
            hud.image.blit(enc, scale_sequence((12, 12)))
            hud.image.blit(cap, scale_sequence((12, 20)))
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
            self.build_animate_hp_bar(monster)

        self.hud[monster] = hud

    def animate_parties_in(self) -> None:
        surface = pygame.display.get_surface()
        x, y, w, h = surface.get_rect()

        # Get background image if passed in
        self.background = self.load_sprite(
            f"gfx/ui/combat/{self.graphics.background}"
        )
        assert self.background

        player, opponent = self.players
        opp_mon = opponent.monsters[0]
        player_home = self._layout[player]["home"][0]
        opp_home = self._layout[opponent]["home"][0]
        y_mod = scale(50)
        duration = 3

        back_island = self.load_sprite(
            f"gfx/ui/combat/{self.graphics.island_back}",
            bottom=opp_home.bottom + y_mod,
            right=0,
        )

        combat_back = ""
        for pla in player.template:
            combat_back = pla.combat_front

        enemy = opp_mon.get_sprite(
            "front",
            bottom=back_island.rect.bottom - scale(12),
            centerx=back_island.rect.centerx,
        )
        self._monster_sprite_map[opp_mon] = enemy
        self.monsters_in_play[opponent].append(opp_mon)
        self.build_hud(self._layout[opponent]["hud"][0], opp_mon)

        self.sprites.add(enemy)

        self.alert(
            T.format(
                "combat_wild_appeared",
                {"name": opp_mon.name.upper()},
            ),
        )

        front_island = self.load_sprite(
            f"gfx/ui/combat/{self.graphics.island_front}",
            bottom=player_home.bottom - y_mod,
            left=w,
        )

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

    def animate_throw_item(self, monster: Monster, item: Item) -> None:
        monster_sprite = self._monster_sprite_map[monster]
        capdev = self.load_sprite(item.sprite)
        animate = partial(
            self.animate, capdev.rect, transition="in_quad", duration=1.0
        )
        graphics.scale_sprite(capdev, 0.4)
        capdev.rect.center = scale(0), scale(0)
        animate(x=monster_sprite.rect.centerx)
        animate(y=monster_sprite.rect.centery)
        self.task(capdev.kill, 1.0)

    def animate_capture_monster(
        self,
        is_captured: bool,
        num_shakes: int,
        monster: Monster,
        item: Item,
        sprite: Sprite,
        combat: ParkState,
    ) -> None:
        """
        Animation for capturing monsters.

        Parameters:
            is_captured: Whether the monster will be captured.
            num_shakes: Number of shakes before animation ends.
            monster: The monster to capture.
            item: Type of tuxeball used.
            sprite: Sprite of the tuxeball.
            combat: ParkState to connect with the class.

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

        combat._captured_mon = monster
        if is_captured:
            value = int(self.players[0].game_variables["menu_park_captured"])
            value += 1
            self.players[0].game_variables["menu_park_captured"] = value
            self.task(kill, 2 + num_shakes)
            action_time = num_shakes + 1.8
            # Tuxepedia: set monster as caught (2)
            if self.players[0].tuxepedia[monster.slug] == SeenStatus.seen:
                combat._new_tuxepedia = True
            self.players[0].tuxepedia[monster.slug] = SeenStatus.caught
            # Display 'Gotcha!' first.
            self.task(combat.end_combat, action_time + 4)
            gotcha = T.translate("gotcha")
            combat._captured = True
            info = None
            # if party
            if len(combat.players[0].monsters) >= 6:
                info = T.format(
                    "gotcha_kennel",
                    {"name": monster.name.upper()},
                )
            else:
                info = T.format(
                    "gotcha_team",
                    {"name": monster.name.upper()},
                )
            if info:
                gotcha += "\n" + info
                action_time += len(gotcha) * 0.02
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
