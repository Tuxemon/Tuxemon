# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""
There are quite a few hacks in here to get this working for single player only
notably, the use of self.game
"""

from __future__ import annotations

import logging
from abc import ABC
from collections.abc import Callable
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
from tuxemon.state.animation_transition import AnimationTransition
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

# EXP bar pacing.
#
# A cubic ease-out, rather than the quintic the rest of the game defaults to
# (see config.py). Both open fast and decelerate to a stop, but a quintic
# opens at five times its average speed against a cubic's three, and spends
# its last 40% of runtime covering the final 1% of travel against a cubic's
# 21%. That suits a sprite thrown across the screen; a gauge wants to arrive
# rather than creep, and matching the two curves' opening speed makes the
# cubic 40% shorter for the same visible fill.
#
# Sweep time is proportional to the distance travelled, which holds that
# opening speed at a constant 3 / EXP_BAR_SWEEP_TIME bar-widths per second
# however much experience was gained; raise the sweep time to lower it.
EXP_BAR_TRANSITION = "out_cubic"
EXP_BAR_SWEEP_TIME = 2.4  # seconds for a full empty -> full sweep
EXP_BAR_MIN_SWEEP_TIME = 0.6  # floor, so a tiny gain is still readable
# A gain worth more than a level or so would run for ten seconds at that pace,
# which is a long time to hold up the battle, so the whole animation is capped
# and its sweeps scaled down to fit. Only a big multi-level gain hits this.
EXP_BAR_MAX_TOTAL_TIME = 4.0
# The ease-out already coasts at the top for a while, so this is only a garnish
# on top of it rather than the whole pause before the bar wraps round.
EXP_BAR_FULL_HOLD = 0.2


def _settle_fraction(transition: str, covered: float = 0.99) -> float:
    """
    How far into an eased animation the travel is, for practical purposes,
    over.

    An ease-out creeps towards its target long after it looks stopped -- a
    quintic spends its last 40% moving the final 1%. Anything scheduled to
    follow the animation should line up with this point, not its nominal end,
    or it waits through motion nobody can see.
    """
    ease = getattr(AnimationTransition, transition)
    steps = 1000
    return next(
        (
            step / steps
            for step in range(steps + 1)
            if ease(step / steps) >= covered
        ),
        1.0,
    )


EXP_BAR_SETTLE = _settle_fraction(EXP_BAR_TRANSITION)


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
        # Levels each monster has gained but not yet shown on its EXP bar.
        # Keyed by the monster itself: two party members can share a slug.
        self.pending_level_ups: dict[Monster, int] = {}
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
            self.bars.remove_monster(monster)

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

    def claim_exp_bar(self, monster: Monster) -> None:
        """
        Reserve a monster's EXP bar for an animation that has not started yet.

        Experience is granted well before ``animate_exp`` runs; without this
        the redraws in between would see the bar disagree with the model and
        snap it straight to the new value, swallowing the animation.
        """
        exp_bar = self.bars.get_exp_bar(monster)
        self.bars.claim(exp_bar, monster.experience_progress_percent)

    @staticmethod
    def exp_bar_sweeps(
        start: float, target: float, levels_gained: int
    ) -> list[tuple[float, float, bool, float]]:
        """
        Plan the sweeps that walk an EXP bar from ``start`` to ``target``.

        Each level gained gets a sweep of its own: the bar fills to the top,
        pauses, wraps back to empty and carries on, so a multi-level gain
        reads as several level-ups rather than one jump. A gain large enough
        to outrun ``EXP_BAR_MAX_TOTAL_TIME`` keeps all its sweeps, scaled to
        fit rather than dropped.

        Returns:
            One ``(value, duration, from_empty, delay)`` tuple per sweep.
        """

        def pace(distance: float) -> float:
            """
            Time to travel `distance`, in proportion to it and with a floor.

            Scaling the time with the distance is what keeps the ease-out's
            opening flick at one speed: a bigger gain takes longer rather
            than moving faster.
            """
            return max(
                EXP_BAR_MIN_SWEEP_TIME, abs(distance) * EXP_BAR_SWEEP_TIME
            )

        sweeps: list[tuple[float, float, bool, float]] = []
        for wrap in range(levels_gained):
            # top up the bar for the level that was just completed...
            from_empty = wrap > 0
            distance = 1.0 if from_empty else 1.0 - start
            sweeps.append(
                (
                    1.0,
                    pace(distance),
                    from_empty,
                    EXP_BAR_FULL_HOLD if from_empty else 0.0,
                )
            )

        # ...then fill in the progress made towards the level after it
        wrapped = levels_gained > 0
        distance = target if wrapped else target - start
        sweeps.append(
            (
                target,
                pace(distance),
                wrapped,
                EXP_BAR_FULL_HOLD if wrapped else 0.0,
            )
        )

        total = sum(duration + delay for _, duration, _, delay in sweeps)
        if total <= EXP_BAR_MAX_TOTAL_TIME:
            return sweeps

        # Too long to sit through: play the same sweeps, proportionally
        # quicker, so the shape of the gain still reads.
        scale = EXP_BAR_MAX_TOTAL_TIME / total
        return [
            (value, duration * scale, from_empty, delay * scale)
            for value, duration, from_empty, delay in sweeps
        ]

    def _pending_exp_sweeps(
        self, monster: Monster
    ) -> list[tuple[float, float, bool, float]]:
        """
        The sweeps ``animate_exp`` will play for the gain awaiting a monster.

        Only valid before ``animate_exp`` runs: it consumes the pending levels
        and moves the bar. Callers use it to schedule around the animation.
        """
        exp_bar = self.bars.get_exp_bar(monster)
        return self.exp_bar_sweeps(
            exp_bar.value,
            monster.experience_progress_percent,
            self.pending_level_ups.get(monster, 0),
        )

    def exp_animation_time(self, monster: Monster) -> float:
        """
        When the EXP bar comes to rest, in seconds from the start of the
        animation.

        This is where the motion ends rather than where the animation does:
        the final sweep's ease-out is still creeping imperceptibly after it,
        and waiting that out would be dead time (see _settle_fraction).
        """
        *earlier, last = self._pending_exp_sweeps(monster)
        _, last_duration, _, last_delay = last
        return (
            sum(duration + delay for _, duration, _, delay in earlier)
            + last_delay
            + last_duration * EXP_BAR_SETTLE
        )

    def exp_first_wrap_time(self, monster: Monster) -> float:
        """
        When the EXP bar will first reach the top, in seconds from the start
        of the animation. That is the moment the new level should be shown.

        Falls back to the end of the motion when no level was gained, since
        then there is no wrap to line up with.
        """
        first_value, duration, _, delay = self._pending_exp_sweeps(monster)[0]
        if first_value < 1.0:
            return self.exp_animation_time(monster)
        return delay + duration * EXP_BAR_SETTLE

    def animate_exp(self, monster: Monster) -> None:
        """Animate a monster's EXP bar up to its current progress."""
        exp_bar = self.bars.get_exp_bar(monster)
        target = monster.experience_progress_percent
        levels_gained = self.pending_level_ups.pop(monster, 0)
        self.bars.claim(exp_bar, target)

        def make_step(
            value: float,
            duration: float,
            from_empty: bool,
            delay: float,
        ) -> Callable[[], Animation]:
            def step() -> Animation:
                ani = self.animate(
                    exp_bar,
                    value=value,
                    duration=duration,
                    transition=EXP_BAR_TRANSITION,
                    # restarting from 0 is what makes the bar wrap around;
                    # the delay holds it at full first, so the wrap is seen
                    initial=0.0 if from_empty else None,
                    delay=delay,
                )
                ani.schedule(self.refresh_ui, ScheduleType.ON_UPDATE)
                ani.schedule(self.refresh_ui, ScheduleType.ON_FINISH)
                # if the chain is cut short, leave the bar telling the truth
                ani.schedule(
                    partial(exp_bar.sync, target), ScheduleType.ON_ABORT
                )
                return ani

            return step

        self.chain_animations(
            *(
                make_step(*sweep)
                for sweep in self.exp_bar_sweeps(
                    exp_bar.value, target, levels_gained
                )
            )
        )

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

        # draw_text resets the HUD to its blank base image, wiping the bars
        # that were composited onto it, so put them back.
        self.refresh_ui()

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
            hud_graphics = (
                hud_model.double_player
                if is_player
                else hud_model.double_opponent
            )
        else:
            hud_graphics = (
                hud_model.hud_player if is_player else hud_model.hud_opponent
            )

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
