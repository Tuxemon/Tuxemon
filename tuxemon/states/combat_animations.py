# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""
There are quite a few hacks in here to get this working for single player only
notably, the use of self.game
"""

from __future__ import annotations

import logging
from abc import ABC
from functools import partial
from typing import TYPE_CHECKING, Any, ClassVar

from pygame.rect import Rect
from pygame.surface import Surface
from pygame.transform import flip as pg_flip

from tuxemon import graphics
from tuxemon.animation import Animation, ScheduleType
from tuxemon.combat.utils import build_hud_text
from tuxemon.constants.paths import mods_folder
from tuxemon.database.rules import config_combat
from tuxemon.environment import BattleLayout
from tuxemon.menu.menu import Menu
from tuxemon.monster.renderer import MonsterRenderer
from tuxemon.platform.const.sizes import PARTY_LIMIT
from tuxemon.sprite import CaptureDeviceSprite, HordeSprite, Sprite
from tuxemon.ui.combat_bars import CombatBars
from tuxemon.ui.combat_hud import CombatLayoutManager
from tuxemon.ui.combat_layout import LayoutManager
from tuxemon.ui.combat_monsters import MonsterSpriteMap
from tuxemon.ui.combat_status import StatusIconManager
from tuxemon.ui.combat_text_display import CombatTextDisplay
from tuxemon.ui.combat_zone import CombatZone
from tuxemon.ui.text_alignment import HorizontalAlignment

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.core.core_effect import ItemEffectResult
    from tuxemon.entity.npc import NPC
    from tuxemon.item.item import Item
    from tuxemon.monster.monster import Monster
    from tuxemon.ui.graphic_box import GraphicBox
    from tuxemon.ui.text import TextArea

logger = logging.getLogger(__name__)

HUD_LAYER = 100

# Timings of the HUD slide-in played when a monster is sent out. Status icons
# sit at the HUD's resting position, so they are only shown once the HUD has
# finished travelling there.
HUD_SLIDE_DELAY = 1.3
HUD_SLIDE_DURATION = 2.0


def toggle_visible(sprite: Sprite) -> None:
    sprite.toggle_visible()


class CombatAnimations(Menu[None], ABC):
    """
    Collection of combat animations.

    Mixin-ish thing until things are sorted out.
    Mostly just a collections of methods to animate the sprites

    These methods should not, without [many] exception[s], manipulate
    game/combat state.  These should just move sprites around
    the screen, with the occasional creation/removal of sprites....
    but never game objects.
    """

    name: ClassVar[str] = "CombatAnimations"

    def __init__(
        self, client: BaseClient, teams: list[NPC], **kwargs: Any
    ) -> None:
        super().__init__(client=client, **kwargs)
        self.combat_session = self.client.combat_session
        self.sprite_map = MonsterSpriteMap()
        self.capdevs: list[CaptureDeviceSprite] = []
        self.horde_sprite: HordeSprite | None = None
        self.bars = CombatBars(self.client.context)
        layout_manager = LayoutManager(
            mods_folder / "combat_layouts.yaml", self.client.context.scaling
        )
        _layout = layout_manager.prepare_all(teams)
        self.hud_manager = CombatLayoutManager(_layout)
        self.status_icons = StatusIconManager(self, _layout, self.hud_manager)
        self.combat_zone = CombatZone(self.client.context.rect)
        self.text_display = CombatTextDisplay(
            get_rect_func=self.hud_manager.get_rect,
            shadow_text_func=self.shadow_text,
        )
        self.background_sprite: Sprite | None = None
        self.monsters_just_leveled_up: dict[str, bool] = {}
        self.monsters_leftover_xp: dict[str, float] = {}
        env = self.client.environment_manager.get_active_environment()
        if env is None:
            raise RuntimeError(
                "Environment not set. Use set_environment before proceeding."
            )
        self.env = env

    def draw(self, surface: Surface) -> None:
        super().draw(surface)

    def refresh_ui(self) -> None:
        """Call this whenever HP or EXP changes."""
        current_graphics = self.env.get_battle_graphics()
        self.bars.draw_bars(self.hud_manager.hud_map, current_graphics)

    def refresh_status_icons(self) -> None:
        """Rebuild the condition icons of every monster on the battlefield."""
        self.status_icons.update_icons_for_monsters(
            self.combat_session.active_monsters
        )

    def show_combat_dialog(
        self, dialog_box: GraphicBox, text_area: TextArea
    ) -> None:
        """Show the area where battle messages are displayed."""
        self.sprites.add(dialog_box, layer=HUD_LAYER)
        self.sprites.add(text_area, layer=HUD_LAYER)

    def transition_none_normal(self) -> None:
        """From newly opened to normal."""
        self.animate_parties_in()

        for player, layout in self.hud_manager.layout.items():
            self.animate_party_hud_in(player, layout["party"][0])

        for player in self.combat_session.players[
            : 2 if self.combat_session.is_trainer_battle else 1
        ]:
            self.task(partial(self.animate_trainer_leave, player), interval=3)

    def blink(self, sprite: Sprite) -> None:
        self.task(partial(toggle_visible, sprite), interval=0.20, times=8)

    def animate_trainer_leave(self, trainer: NPC | Monster) -> None:
        """Animate the trainer leaving the screen."""
        sprite = self.sprite_map.get_sprite(trainer)
        if sprite is None:
            raise KeyError(f"Sprite not found for entity: {trainer.name}")

        graphics = self.env.get_battle_graphics()
        dist = self.scale_int(-graphics.trainer_exit_offset)
        duration = graphics.trainer_exit_duration
        x_offset = self.combat_zone.get_horizontal_offset(sprite.rect, dist)
        self.animate(sprite.rect, x=x_offset, relative=True, duration=duration)

    def animate_monster_release(
        self,
        npc: NPC,
        monster: Monster,
        sprite: Sprite,
    ) -> None:
        """
        Animates the release of a monster from a capture device.

        This function coordinates the animation of the capture device falling, the
        monster sprite moving into position, and the capture device opening animation.
        It also plays the combat call sound.
        """
        self.hud_manager.assign(
            self.combat_session.count_players,
            npc,
            monster,
            self.combat_session.is_double,
        )
        feet = self.hud_manager.get_feet_position(npc, monster)

        # Load and scale capture device sprite
        capdev = self.load_sprite(f"gfx/items/{monster.capture_device}.png")
        graphics.scale_sprite(capdev, 0.4)
        capdev.rect.center = (feet[0], feet[1] - self.scale_int(60))

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
        animate_fade(capdev.rect, y=-self.scale_int(14), relative=True)

        # Convert capture device sprite for easy fading
        def convert_sprite() -> None:
            capdev.image = graphics.convert_alpha_to_colorkey(capdev.image)
            self.animate(
                capdev.image,
                set_alpha=0,
                initial=255,
                duration=fade_duration,
            )

        self.task(convert_sprite, interval=delay)
        self.task(capdev.kill, interval=fall_time + delay + fade_duration)

        # Load monster sprite and set final position
        renderer = MonsterRenderer(monster, scale=self.factor)
        monster_sprite = renderer.get_sprite(
            "back" if npc == self.combat_session.left_player else "front"
        )
        monster_sprite.rect.midbottom = feet
        self.sprites.add(monster_sprite)
        self.sprite_map.add_sprite(monster, monster_sprite)

        # Position monster sprite off screen and animate it to final spot
        monster_sprite.rect.top = self.client.context.screen.get_height()
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
        self.task(sprite.animation.play, interval=1.3)
        self.task(partial(self.sprites.add, sprite), interval=1.3)

        # Load and play combat call sound
        sound, volume = renderer.get_combat_sound()

        self.event_bus.publish(
            "play_sound_combat",
            sound=sound,
            value=volume,
        )

    def animate_sprite_tackle(self, attacker: Sprite) -> None:
        duration = 0.3
        original_x = attacker.rect.x
        _, horizontal = self.combat_zone.get_zone(attacker.rect)

        delta = (
            self.scale_int(14)
            if horizontal is HorizontalAlignment.LEFT
            else -self.scale_int(14)
        )

        self.animate(
            attacker.rect,
            x=original_x + delta,
            duration=duration,
            transition="out_circ",
            yoyo=True,
            yoyo_loops=1,
        )

    def animate_monster_faint(self, monster: Monster) -> None:
        """Animate a monster fainting and remove it."""

        def kill_monster() -> None:
            """Remove the monster's sprite and HUD elements."""
            self.sprite_map.remove_sprite(monster)
            self.status_icons.remove_monster_icons(monster)
            self.hud_manager.delete_hud(monster)

        self.animate_monster_leave(monster)
        self.task(kill_monster, interval=2)

        for (
            monsters
        ) in self.combat_session.field_monsters.get_all_monsters().values():
            if monster in monsters:
                monsters.remove(monster)

        self.animate_update_horde_hud()
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
        ani = animate(x=original_x, initial=original_x + self.scale_int(400))
        # just want the end of the animation, not the entire thing
        ani._elapsed = 0.735
        ani = animate(y=original_y, initial=original_y - self.scale_int(400))
        # just want the end of the animation, not the entire thing
        ani._elapsed = 0.735

    def animate_hp(self, monster: Monster) -> None:
        hp_bar = self.bars.get_hp_bar(monster)

        ani = Animation(
            hp_bar,
            value=monster.hp_ratio,
            duration=0.7,
            transition="out_quint",
        )

        ani.schedule(self.refresh_ui, ScheduleType.ON_UPDATE)
        ani.schedule(self.refresh_ui, ScheduleType.ON_FINISH)
        self.animations.add(ani)

    def animate_exp(self, monster: Monster) -> None:
        exp_bar = self.bars.get_exp_bar(monster)
        value_for_new_level = monster.experience_progress_percent

        def register(ani: Animation) -> Animation:
            ani.schedule(self.refresh_ui, ScheduleType.ON_UPDATE)
            self.animations.add(ani)
            return ani

        # Level-up case
        if self.monsters_just_leveled_up.get(monster.slug, False):
            # leftover percent is already correct in the model
            leftover = value_for_new_level

            def animate_new_level_progress() -> Animation:
                # do NOT reset exp_bar.value to 0
                ani = register(
                    self.animate(
                        exp_bar,
                        value=leftover,
                        duration=0.7,
                        transition="linear",
                        delay=0.5,
                    )
                )
                ani.schedule(self.refresh_ui, ScheduleType.ON_FINISH)
                return ani

            # optional: keep the fill-to-max animation
            def fill_to_max() -> Animation:
                ani = register(
                    self.animate(
                        exp_bar,
                        value=1.0,
                        duration=0.3,
                        transition="linear",
                    )
                )
                ani.schedule(self.refresh_ui, ScheduleType.ON_FINISH)
                return ani

            # chain both animations
            self.chain_animations(fill_to_max, animate_new_level_progress)
            self.monsters_just_leveled_up[monster.slug] = False

        else:
            # normal XP gain
            ani = register(
                self.animate(
                    exp_bar,
                    value=value_for_new_level,
                    duration=0.7,
                    transition="out_quint",
                )
            )
            ani.schedule(self.refresh_ui, ScheduleType.ON_FINISH)

    def animate_monster_leave(self, monster: Monster) -> None:
        sprite = self.sprite_map.get_sprite(monster)
        if sprite is None:
            raise KeyError(f"Sprite not found for entity: {monster.name}")

        x_offset = self.combat_zone.get_horizontal_offset(
            sprite.rect, self.scale_int(-150)
        )

        renderer = MonsterRenderer(monster)

        if monster.current_hp > 0:
            sound, volume = renderer.get_combat_sound()
        else:
            sound, volume = renderer.get_faint_sound()

        self.event_bus.publish(
            "play_sound_combat",
            sound=sound,
            value=volume,
        )
        self.animate(sprite.rect, x=x_offset, relative=True, duration=2)
        self.status_icons.animate_icons(monster, self.animate)

    def _update_hud_details(
        self, monster: Monster, hud: Sprite, is_player: bool
    ) -> None:
        """
        Gathers data and delegates drawing of text labels to CombatTextDisplay.
        """
        owner = monster.get_owner()
        trainer_battle = self.combat_session.is_trainer_battle

        symbol = False
        if not is_player:
            left_player = self.combat_session.left_player
            if left_player.tuxepedia.is_caught(monster.slug):
                symbol = True

        label_data = build_hud_text(
            self.env.get_battle_graphics().menu,
            monster,
            is_player,
            trainer_battle,
            symbol,
        )

        self.text_display.draw_text(
            hud=hud,
            owner=owner,
            label_data=label_data,
        )

    def check_hud(
        self, monster: Monster, filename: str, layer: int = HUD_LAYER
    ) -> Sprite:
        """
        Checks whether exists or not a hud, it returns a sprite.
        To avoid building over an existing one.

        Parameters:
            monster: Monster who needs to update the hud.
            filename: Filename of the hud.
            layer: Layer the hud is drawn on.
        """
        sprite = self.hud_manager.get_hud(monster)
        if sprite is None:
            sprite = self.load_sprite(filename, layer=layer)
        elif self.sprites.get_layer_of_sprite(sprite) != layer:
            self.sprites.change_layer(sprite, layer)

        return sprite

    def build_hud(
        self, monster: Monster, hud_position: str, animate: bool = True
    ) -> None:
        """
        Builds the HUD for a monster, focusing on creation and animation.
        """
        owner = monster.get_owner()
        hud_rect = self.hud_manager.get_rect(owner, hud_position)

        _, h_align = self.combat_zone.get_zone(hud_rect)
        is_player = h_align is HorizontalAlignment.RIGHT

        hud_model = self.env.get_battle_graphics().hud
        if self.combat_session.is_double:
            hud_graphics = hud_model.double_player if is_player else hud_model.double_opponent
        else:
            hud_graphics = hud_model.hud_player if is_player else hud_model.hud_opponent

        layer = self.hud_manager.get_hud_layer(monster, HUD_LAYER)
        hud = self.check_hud(monster, hud_graphics, layer)
        hud.base_image = hud.image.copy()
        hud.player = is_player
        self.hud_manager.assign_hud(monster, hud)

        self._update_hud_details(monster, hud, is_player)

        if is_player:
            hud.rect.bottomleft = hud_rect.right, hud_rect.bottom
        else:
            hud.rect.bottomright = 0, hud_rect.bottom

        if animate:
            target_pos = (
                {"left": hud_rect.left}
                if is_player
                else {"right": hud_rect.right}
            )
            animate_func = partial(
                self.animate,
                duration=HUD_SLIDE_DURATION,
                delay=HUD_SLIDE_DELAY,
            )
            slide = animate_func(hud.rect, **target_pos)
            # A monster can arrive already carrying a condition, so show its
            # icons as soon as the HUD reaches its resting place rather than
            # waiting for the next status to be applied.
            slide.schedule(self.refresh_status_icons, ScheduleType.ON_FINISH)

            self.animate_hp(monster)
            if hud.player:
                self.animate_exp(monster)
        else:
            if is_player:
                hud.rect.left = hud_rect.left
            else:
                hud.rect.right = hud_rect.right
            self.refresh_status_icons()

    def _load_sprite(
        self, sprite_type: str, position: dict[str, int]
    ) -> Sprite:
        return self.load_sprite(sprite_type, **position)

    def animate_party_hud_left(
        self, home: Rect
    ) -> tuple[Sprite | None, int, int]:
        if not (
            self.combat_session.is_trainer_battle
            and not self.combat_session.is_double
        ):
            return (
                None,
                home.right - self.scale_int(13),
                self.scale_int(8),
            )

        hud_data = self.env.data.get_battle_graphics().hud
        party_layout = self.env.get_party_layout("opponent", home, HUD_LAYER)

        tray = self._load_sprite(party_layout.path, party_layout.init_pos)
        self.animate(
            tray.rect,
            duration=hud_data.animation_duration,
            delay=hud_data.animation_delay,
            **party_layout.target,
        )

        return tray, party_layout.centerx, party_layout.offset

    def animate_party_hud_right(
        self, home: Rect
    ) -> tuple[Sprite | None, int, int]:
        if self.combat_session.is_double:
            return (
                None,
                home.left + self.scale_int(13),
                self.scale_int(8),
            )
        hud_data = self.env.data.get_battle_graphics().hud
        party_layout = self.env.get_party_layout("player", home, HUD_LAYER)

        tray = self._load_sprite(party_layout.path, party_layout.init_pos)
        self.animate(
            tray.rect,
            duration=hud_data.animation_duration,
            delay=hud_data.animation_delay,
            **party_layout.target,
        )

        return tray, party_layout.centerx, party_layout.offset

    def animate_party_hud_in(self, player: NPC, home: Rect) -> None:
        """
        Animates the party HUD (the arrow thing with balls).

        Parameters:
            player: The player whose HUD is being animated.
            home: Location and size of the HUD.
        """
        _, h_align = self.combat_zone.get_zone(home)

        is_opponent_horde = (
            player is self.combat_session.right_player
            and self.combat_session.is_horde_battle
        )

        if is_opponent_horde:
            tray, _, _ = self.animate_party_hud_left(home)

            self.horde_sprite = HordeSprite(
                opponent_party=player.party,
                tray_rect=home,
                shadow_text_func=self.shadow_text,
                context=self.client.context,
            )
            self.sprites.add(self.horde_sprite, layer=HUD_LAYER)

            animate_func = partial(self.animate, duration=2.0, delay=1.5)
            self.horde_sprite.animate_in(animate_func)
            return

        if h_align is HorizontalAlignment.LEFT:
            tray, centerx, offset = self.animate_party_hud_left(home)
        else:
            tray, centerx, offset = self.animate_party_hud_right(home)

        if tray is None or any(t.wild for t in player.monsters):
            return

        monster_count = player.party.party_size
        positions = (
            [monster_count - i - 1 for i in range(PARTY_LIMIT)]
            if h_align is HorizontalAlignment.LEFT
            else list(range(PARTY_LIMIT))
        )

        scaled_top = self.factor

        for index, pos in enumerate(positions):
            monster = player.monsters[index] if index < monster_count else None
            centerx_pos = centerx - (pos if monster else index) * offset

            sprite = self._load_sprite(
                self.env.get_battle_graphics().icons.icon_empty,
                {
                    "top": tray.rect.top + scaled_top,
                    "centerx": centerx_pos,
                    "layer": HUD_LAYER,
                },
            )

            capdev = CaptureDeviceSprite(
                sprite=sprite,
                tray=tray,
                monster=monster,
                icon=self.env.get_battle_graphics().icons,
                context=self.client.context,
            )
            self.capdevs.append(capdev)
            animate = partial(
                self.animate, duration=1.5, delay=2.2 + index * 0.2
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

    def animate_update_horde_hud(self) -> None:
        """
        Update the horde HUD to reflect the horde.
        """
        if self.combat_session.is_horde_battle and self.horde_sprite:
            if self.horde_sprite.update_count_display():
                animate_func = partial(self.animate, duration=2.0, delay=1.5)
                self.horde_sprite.animate_in(animate_func)
            if self.horde_sprite.is_defeated():
                self.task(self.horde_sprite.kill, interval=2)
                self.horde_sprite = None

    def render_background(self) -> None:
        if self.background_sprite:
            self.background_sprite.kill()

        full_surf = self.env.prepare_background(self.client.context.rect.size)
        spr = Sprite()
        spr.image = full_surf
        spr.rect = full_surf.get_rect()
        spr.rect.topleft = (0, 0)
        self.sprites.add(spr, layer=0)
        self.background_sprite = spr

    def animate_parties_in(self) -> None:
        """Animate the parties entering the battle scene."""
        self.render_background()

        player, opponent = self.combat_session.players
        opp_mon = opponent.monsters[0]

        # Setup Layout
        self.hud_manager.assign(
            self.combat_session.count_players,
            opponent,
            opp_mon,
            self.combat_session.is_double,
        )
        player_home = self.hud_manager.get_rect(player, "home")
        opp_home = self.hud_manager.get_rect(opponent, "home")
        layout = self.env.get_battle_layout(
            self.client.context.rect.size, player_home, opp_home
        )

        # Spawn Islands
        assets = self.env.get_battle_assets()
        back_island = self.load_surface(
            assets["island_back"], **layout.back_island_pos
        )
        front_island = self.load_surface(
            assets["island_front"], **layout.front_island_pos
        )

        # Spawn Entities
        if self.combat_session.is_trainer_battle:
            enemy_pos = layout.get_combatant_pos("enemy", back_island.rect)
            enemy_surface = opponent.combat_sheet.front()
            enemy_surface = graphics.scale_surface(enemy_surface, self.factor)
            enemy = self.load_surface(enemy_surface, **enemy_pos)
            self.sprite_map.add_sprite(opponent, enemy)
        else:
            monster_pos = layout.get_combatant_pos("monster", back_island.rect)
            renderer = MonsterRenderer(opp_mon, scale=self.factor)
            enemy = renderer.get_sprite("front")
            enemy.rect.midbottom = (
                monster_pos["centerx"],
                monster_pos["bottom"],
            )
            self.sprite_map.add_sprite(opp_mon, enemy)
            self.combat_session.field_monsters.add_monster(opponent, opp_mon)
            self.update_hud(opponent, True, True)

        player_pos = layout.get_combatant_pos("player", front_island.rect)
        # Bring the trainer on lower so the (taller) back sprite sits on the
        # island rather than floating above it. 64 is a nominal value, scaled
        # to the current display.
        player_pos["bottom"] += self.scale_int(64)
        player_surface = player.combat_sheet.back()
        player_surface = graphics.scale_surface(player_surface, self.factor)
        player_back = self.load_surface(player_surface, **player_pos)

        self.sprites.add(enemy, player_back)
        self.sprite_map.add_sprite(player, player_back)
        self.flip_sprites(enemy, player_back)
        self.animate_sprites(
            layout, enemy, back_island, front_island, player_back
        )

        if not self.combat_session.is_trainer_battle:
            renderer = MonsterRenderer(opp_mon)
            sound, volume = renderer.get_combat_sound()

            self.event_bus.publish(
                "play_sound_combat",
                sound=sound,
                value=volume,
            )

        self.event_bus.publish(
            "combat_dialog", message=self.combat_session.get_start_message()
        )

    def flip_sprites(self, enemy: Sprite, player_back: Sprite) -> None:
        """Flip the sprites horizontally."""

        def flip() -> None:
            enemy.image = pg_flip(enemy.image, True, False)
            player_back.image = pg_flip(player_back.image, True, False)

        flip()
        self.task(flip, interval=1.5)

    def animate_sprites(
        self,
        layout: BattleLayout,
        enemy: Sprite,
        back_island: Sprite,
        front_island: Sprite,
        player_back: Sprite,
    ) -> None:
        """Animate the sprites."""
        y_mod = layout.entry_jump_distance
        duration = layout.entry_duration

        animate = partial(
            self.animate, transition="out_quad", duration=duration
        )

        # Move islands/sprites to their HUD home positions
        pos_opp = self.hud_manager.get_rect(
            self.combat_session.right_player, "home"
        )
        animate(enemy.rect, back_island.rect, centerx=pos_opp.centerx)
        animate(
            enemy.rect,
            back_island.rect,
            y=-y_mod,
            transition="out_back",
            relative=True,
        )

        pos_pla = self.hud_manager.get_rect(
            self.combat_session.left_player, "home"
        )
        animate(player_back.rect, front_island.rect, centerx=pos_pla.centerx)
        animate(
            player_back.rect,
            front_island.rect,
            y=y_mod,
            transition="out_back",
            relative=True,
        )

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
        monster_sprite = self.sprite_map.get_sprite(monster)
        if monster_sprite is None:
            raise KeyError(f"Sprite not found for entity: {monster.name}")
        sprite = self.load_sprite(item.sprite)
        animate = partial(
            self.animate, sprite.rect, transition="in_quad", duration=1.0
        )
        graphics.scale_sprite(sprite, 0.4)
        sprite.rect.center = self.scale_int(0), self.scale_int(0)
        animate(x=monster_sprite.rect.centerx)
        animate(y=monster_sprite.rect.centery)
        return sprite

    def animate_capture_monster(
        self,
        result: ItemEffectResult,
        monster: Monster,
        item: Item,
        sprite: Sprite,
        texts: tuple[str, str, str],
    ) -> None:
        """
        Animation for capturing monsters.

        Parameters:
            result: Result of the capture plugin.
            monster: The monster being captured.
            item: The capture device used to capture the monster.
            sprite: The sprite to animate.
            messages: Success header, success and failture text.
        """
        num_shakes = result.num_shakes
        is_captured = result.success
        success_header, success_body, failure_text = texts
        monster_sprite = self.sprite_map.get_sprite(monster)
        if monster_sprite is None:
            raise KeyError(f"Sprite not found for entity: {monster.name}")

        capdev = self.animate_throwing(monster, item)
        hit_time = 1.0
        self.task(partial(toggle_visible, monster_sprite), interval=hit_time)

        if sprite.animation:
            self.task(sprite.animation.play, interval=hit_time)
            self.task(partial(self.sprites.add, sprite), interval=hit_time)

        sprite.rect.midbottom = monster_sprite.rect.midbottom

        def shake_up() -> Animation:
            return self.animate(
                capdev.rect,
                y=self.scale_int(3),
                relative=True,
                duration=0.1,
                transition="in_quad",
            )

        def shake_down() -> Animation:
            return self.animate(
                capdev.rect,
                y=-self.scale_int(6),
                relative=True,
                duration=0.2,
                transition="in_quad",
            )

        def shake_up2() -> Animation:
            return self.animate(
                capdev.rect,
                y=self.scale_int(3),
                relative=True,
                duration=0.1,
                transition="in_quad",
            )

        for i in range(num_shakes):
            start = 1.8 + i * 1.0
            self.chain_animations(
                shake_up, shake_down, shake_up2, start_delay=start
            )

        breakout_time = 1.8 + num_shakes * 1.0

        # SUCCESS CASE
        if is_captured:

            def kill_monster() -> None:
                self.sprite_map.remove_sprite(monster)
                self.hud_manager.delete_hud(monster)

            self.task(kill_monster, interval=2 + num_shakes)

            full_msg = f"{success_header}\n{success_body}"

            msg_delay = num_shakes / 2
            dialog_delay = (
                num_shakes
                + msg_delay
                + len(full_msg) * config_combat.letter_time
            )

            def show_success() -> None:
                self.event_bus.publish("combat_dialog", message=full_msg)

            self.task(show_success, interval=dialog_delay)

            self.task(
                partial(self.event_bus.publish, "clean_combat"),
                interval=dialog_delay + 4,
            )

        # FAILURE CASE
        else:

            def show_monster() -> None:
                toggle_visible(monster_sprite)
                renderer = MonsterRenderer(monster)
                sound, volume = renderer.get_combat_sound()

                self.event_bus.publish(
                    "play_sound_combat",
                    sound=sound,
                    value=volume,
                )

            def capture_capsule() -> None:
                if sprite.animation:
                    sprite.animation.play()
                capdev.kill()

            def blink_monster() -> None:
                self.blink(sprite)

            def show_failure() -> None:
                self.event_bus.publish("combat_dialog", message=failure_text)

            self.task(show_monster, interval=breakout_time)
            self.task(capture_capsule, interval=breakout_time)
            self.task(blink_monster, interval=breakout_time + 0.5)

            failure_delay = (
                breakout_time + len(failure_text) * config_combat.letter_time
            )
            self.task(show_failure, interval=failure_delay)

            full_msg = failure_text

        callback_delay = (
            breakout_time + len(full_msg) * config_combat.letter_time + 1.0
        )

        self.task(
            lambda: self.event_bus.publish(
                "capture_finished", monster=monster, is_captured=is_captured
            ),
            interval=callback_delay,
        )

    def update_hud(self, character: NPC, animate: bool, delete: bool) -> None:
        """
        Updates the Heads-Up Display (HUD) for monsters belonging to the given character.

        Parameters:
            character: The character whose monsters' HUDs should be refreshed.
            animate: Whether to animate HUD transitions.
            delete: Whether to delete existing HUDs before updating.
        """
        monsters = self.combat_session.field_monsters.get_monsters(character)
        if not monsters:
            return

        # Cleanup old HUDs if requested
        if delete:
            for monster in monsters:
                self.hud_manager.delete_hud(monster)

        # Assign and Build HUDs
        # If there is only 1 monster, we use the ID "hud".
        # If there are multiple, we use "hud0", "hud1", etc. The slot comes
        # from the layout manager rather than the order of this list, which
        # is ordered by entry time: a monster entering after its ally would
        # otherwise get the HUD (and the status icons anchored to it) of the
        # slot it isn't standing in.
        for monster in monsters:
            hud_id = self.hud_manager.get_hud_key(monster)
            self.build_hud(monster, hud_id, animate)