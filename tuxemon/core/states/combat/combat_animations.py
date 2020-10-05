"""
There are quite a few hacks in here to get this working for single player only
notably, the use of self.game
"""


import logging
from functools import partial

import pygame

from tuxemon.compat import Rect
from tuxemon.core import audio, graphics, tools
from tuxemon.core.locale import T
from tuxemon.core.menu.interface import HpBar, ExpBar
from tuxemon.core.menu.menu import Menu
from tuxemon.core.pyganim import PygAnimation
from tuxemon.core.sprite import Sprite, CaptureDeviceSprite
from tuxemon.core.tools import scale, scale_sequence

logger = logging.getLogger(__name__)

sprite_layer = 0
hud_layer = 100
monster_hud_move_in_time = 2


def toggle_visible(sprite):
    sprite.visible = not sprite.visible


def scale_area(area):
    return Rect(tools.scale_sequence(area))


class CombatAnimations(Menu):
    """ Mixin-ish thing until things are sorted out.
        Mostly just a collections of methods to animate the sprites

        These methods should not, without [many] exception[s], manipulate
        game/combat state.  These should just move sprites around
        the screen, with the occasional creation/removal of sprites....
        but never game objects.
    """

    def startup(self, **kwargs):
        super().startup(**kwargs)
        self._monster_sprite_map = dict()
        self.hud = dict()
        self.is_trainer_battle = None
        self.capdevs = list()

        # eventually store in a config somewhere
        # is a tuple because more areas is needed for multi monster, etc
        layout = list()

        player = dict()
        player['home'] = ((0, 62, 95, 70),)
        player['hud'] = ((145, 45, 110, 50),)
        player['party'] = ((152, 57, 110, 50),)
        layout.append(player)

        opponent = dict()
        opponent['home'] = ((140, 10, 95, 70),)
        opponent['hud'] = ((18, 0, 85, 30),)
        opponent['party'] = ((18, 12, 85, 30),)
        layout.append(opponent)
        # end config =========================================

        # convert the list/tuple of coordinates to Rects
        for position in layout:
            for key, value in position.items():
                position[key] = list(map(scale_area, value))

        # map positions to players
        self._layout = dict()
        for index, player in enumerate(self.players):
            self._layout[player] = layout[index]

    def animate_open(self):
        self.transition_none_normal()

    def transition_none_normal(self):
        """ From newly opened to normal
        """
        self.animate_parties_in()

        for player, layout in self._layout.items():
            self.animate_party_hud_in(player, layout['party'][0])

        self.task(partial(self.animate_trainer_leave, self.players[0]), 3)

        if self.is_trainer_battle:
            self.task(partial(self.animate_trainer_leave, self.players[1]), 3)

    def blink(self, sprite):
        """

        :param sprite: tuxemon.core.sprite.Sprite
        :return:
        """
        self.task(partial(toggle_visible, sprite), .20, 8)

    def animate_trainer_leave(self, trainer):
        """

        :type trainer: tuxemon.core.player.Player
        :return:
        """
        sprite = self._monster_sprite_map[trainer]
        if self.get_side(sprite.rect) == "left":
            x_diff = -scale(150)
        else:
            x_diff = scale(150)

        self.animate(sprite.rect, x=x_diff, relative=True, duration=.8)

    def animate_monster_release(self, npc, monster):
        """

        :type npc: tuxemon.core.npc.Npc
        :type monster: tuxemon.core.monster.Monster
        :return:
        """
        feet = list(self._layout[npc]['home'][0].center)
        feet[1] += tools.scale(11)

        capdev = self.load_sprite('gfx/items/capture_device.png')
        graphics.scale_sprite(capdev, .4)
        capdev.rect.center = feet[0], feet[1] - scale(60)

        # animate the capdev falling
        fall_time = .7
        animate = partial(self.animate, duration=fall_time, transition='out_quad')
        animate(capdev.rect, bottom=feet[1], transition='in_back')
        animate(capdev, rotation=720, initial=0)

        # animate the capdev fading away
        delay = fall_time + .6
        fade_duration = .9
        h = capdev.rect.height
        animate = partial(self.animate, duration=fade_duration, delay=delay)
        animate(capdev, width=1, height=h * 1.5)
        animate(capdev.rect, y=-scale(14), relative=True)

        # convert the capdev sprite so we can fade it easily
        def func():
            capdev.image = graphics.convert_alpha_to_colorkey(capdev.image)
            self.animate(capdev.image, set_alpha=0, initial=255, duration=fade_duration)

        self.task(func, delay)
        self.task(capdev.kill, fall_time + delay + fade_duration)

        # load monster and set in final position
        monster_sprite = monster.get_sprite("back" if npc.isplayer else "front",
                                            midbottom=feet)
        self.sprites.add(monster_sprite)
        self._monster_sprite_map[monster] = monster_sprite

        # position monster_sprite off screen and set animation to move it back to final spot
        monster_sprite.rect.top = self.client.screen.get_height()
        self.animate(monster_sprite.rect, bottom=feet[1], transition='out_back',
                     duration=.9, delay=fall_time + .5)

        # capdev opening animation
        images = list()
        for fn in ["capture%02d.png" % i for i in range(1, 10)]:
            fn = 'animations/technique/' + fn
            image = graphics.load_and_scale(fn)
            images.append((image, .07))

        delay = 1.3
        tech = PygAnimation(images, False)
        sprite = Sprite()
        sprite.image = tech
        sprite.rect = tech.get_rect()
        sprite.rect.midbottom = feet
        self.task(tech.play, delay)
        self.task(partial(self.sprites.add, sprite), delay)

        # attempt to load and queue up combat_call
        call_sound = audio.load_sound(monster.combat_call)
        if call_sound:
            self.task(call_sound.play, delay)



    def animate_sprite_spin(self, sprite):
        """

        :type sprite: tuxemon.core.sprite.Sprite
        :return:
        """
        self.animate(sprite, rotation=360, initial=0, duration=.8, transition='in_out_quint')

    def animate_sprite_tackle(self, sprite):
        """

        :type sprite: tuxemon.core.sprite.Sprite
        :return:
        """
        duration = .3
        original_x = sprite.rect.x

        if self.get_side(sprite.rect) == "left":
            delta = scale(14)
        else:
            delta = -scale(14)

        self.animate(sprite.rect, x=original_x + delta, duration=duration, transition='out_circ')
        self.animate(sprite.rect, x=original_x, duration=duration, transition='in_out_circ', delay=.35)

    def animate_monster_faint(self, monster):
        # TODO: rename to distinguish fainting/leaving
        def kill():
            self._monster_sprite_map[monster].kill()
            self.hud[monster].kill()
            del self._monster_sprite_map[monster]
            del self.hud[monster]

        self.animate_monster_leave(monster)
        self.suppress_phase_change(2)
        self.task(kill, 2)

        for monsters in self.monsters_in_play.values():
            try:
                monsters.remove(monster)
            except ValueError:
                pass

        # update tuxemon balls to reflect fainted tuxemon
        for player, layout in self._layout.items():
            self.animate_update_party_hud(player, layout['party'][0])

    def animate_sprite_take_damage(self, sprite):
        """

        :type sprite: tuxemon.core.sprite.Sprite
        :return:
        """
        original_x, original_y = sprite.rect.topleft
        animate = partial(self.animate, sprite.rect, duration=1, transition='in_out_elastic')
        ani = animate(x=original_x, initial=original_x + scale(400))
        ani._elapsed = .735  # just want the end of the animation, not the entire thing
        ani = animate(y=original_y, initial=original_y - scale(400))
        ani._elapsed = .735  # just want the end of the animation, not the entire thing

    def animate_hp(self, monster):
        """

        :type monster: tuxemon.core.monster.Monster
        :return:
        """
        value = monster.current_hp / monster.hp
        hp_bar = self._hp_bars[monster]
        self.animate(hp_bar, value=value, duration=.7, transition='out_quint')

    def build_animate_hp_bar(self, monster, initial=0):
        """

        :param initial: Starting HP
        :type monster: tuxemon.core.monster.Monster
        :return:
        """
        self._hp_bars[monster] = HpBar(initial)
        self.animate_hp(monster)

    def animate_exp(self, monster):
        """

        :type monster: tuxemon.core.monster.Monster
        :return:
        """
        target_previous = monster.experience_required()
        target_next = monster.experience_required(1)
        value = max(0, min(1, (monster.total_experience - target_previous) / (target_next - target_previous)))
        exp_bar = self._exp_bars[monster]
        self.animate(exp_bar, value=value, duration=.7, transition='out_quint')

    def build_animate_exp_bar(self, monster, initial=0):
        """

        :param initial: Starting EXP
        :type monster: tuxemon.core.monster.Monster
        :return:
        """
        self._exp_bars[monster] = ExpBar(initial)
        self.animate_exp(monster)

    def build_hud_text(self, monster):
        """ Return a string for use on the callout of the monster

        :type monster: tuxemon.core.monster.Monster
        :return:
        """
        return self.shadow_text("{0.name: <12}Lv.{0.level: >2}".format(monster))

    def get_side(self, rect):
        """ [WIP] get 'side' of screen rect is in

        :type rect: Rect
        :return: basestring
        """
        return "left" if rect.centerx < scale(100) else "right"

    def animate_monster_leave(self, monster):
        """

        :type monster: tuxemon.core.monster.Monster
        :return:
        """
        sprite = self._monster_sprite_map[monster]
        if self.get_side(sprite.rect) == "left":
            x_diff = -scale(150)
        else:
            x_diff = scale(150)

        cry = monster.combat_call if monster.current_hp > 0 else monster.faint_call
        sound = audio.load_sound(cry)
        sound.play()
        self.animate(sprite.rect, x=x_diff, relative=True, duration=2)

    def build_hud(self, home, monster):
        """

        :type home: Rect
        :type monster: tuxemon.core.monster.Monster
        :return:
        """

        def build_left_hud():
            hud = self.load_sprite('gfx/ui/combat/hp_opponent_nohp.png', layer=hud_layer)
            hud.image.blit(text, scale_sequence((5, 5)))
            hud.rect.bottomright = 0, home.bottom
            hud.player = False
            animate(hud.rect, right=home.right)
            return hud

        def build_right_hud():
            hud = self.load_sprite('gfx/ui/combat/hp_player_nohp.png', layer=hud_layer)
            hud.image.blit(text, scale_sequence((12, 4)))
            hud.rect.bottomleft = home.right, home.bottom
            hud.player = True
            animate(hud.rect, left=home.left)
            return hud

        text = self.build_hud_text(monster)
        animate = partial(self.animate, duration=monster_hud_move_in_time, delay=1.3)
        if self.get_side(home) == "right":
            hud = build_right_hud()
        else:
            hud = build_left_hud()
        self.hud[monster] = hud

        self.build_animate_hp_bar(monster)
        if hud.player:
            self.build_animate_exp_bar(monster)

    def animate_party_hud_in(self, player, home):
        """ Party HUD is the arrow thing with balls.  Yes, that one.

        :param player: the player
        :type home: Rect
        :param slots: Number of slots
        :return:
        """
        if self.get_side(home) == "left":
            tray = self.load_sprite('gfx/ui/combat/opponent_party_tray.png',
                                    bottom=home.bottom, right=0, layer=hud_layer)
            self.animate(tray.rect, right=home.right, duration=2, delay=1.5)
            centerx = home.right - scale(13)
            offset = scale(8)

        else:
            tray = self.load_sprite('gfx/ui/combat/player_party_tray.png',
                                    bottom=home.bottom, left=home.right, layer=hud_layer)
            self.animate(tray.rect, left=home.left, duration=2, delay=1.5)
            centerx = home.left + scale(13)
            offset = -scale(8)

        for index in range(player.party_limit):
            status = None
            #opponent tuxemon should order from left to right
            if(self.get_side(home) == "left"):
                pos = len(player.monsters)-index-1
            else:
                pos = index
            if len(player.monsters) > index:
                monster = player.monsters[index]
                if any(t for t in monster.status if t.slug == "status_faint"):
                    status = "faint"
                    sprite = self.load_sprite('gfx/ui/icons/party/party_icon03.png',
                                              top=tray.rect.top + scale(1),
                                              centerx=centerx - pos * offset,
                                              layer=hud_layer)
                elif len(monster.status) > 0:
                    status = "effected"
                    sprite = self.load_sprite('gfx/ui/icons/party/party_icon02.png',
                                              top=tray.rect.top + scale(1),
                                              centerx=centerx - pos * offset,
                                              layer=hud_layer)
                else:
                    status = "alive"
                    sprite = self.load_sprite('gfx/ui/icons/party/party_icon01.png',
                                              top=tray.rect.top + scale(1),
                                              centerx=centerx - pos * offset,
                                              layer=hud_layer)
            else:
                status = "empty"
                monster = None
                sprite = self.load_sprite('gfx/ui/combat/empty_slot_icon.png',
                                          top=tray.rect.top + scale(1),
                                          centerx=centerx - index * offset,
                                          layer=hud_layer)
            capdev = CaptureDeviceSprite(sprite = sprite, tray = tray, monster = monster, state = status)
            self.capdevs.append(capdev)
            animate = partial(self.animate, duration=1.5, delay=2.2 + index * .2)
            capdev.draw(animate)


    def animate_update_party_hud(self, player, home):
        """ Party HUD is the arrow thing with balls.  Yes, that one.

        This function updates the balls to reflect how many Tuxemon have fainted.

        :param player: the player
        :type home: Rect
        :param slots: Number of slots
        :return:
        """
        for dev in self.capdevs:
            prev = dev.state
            if(prev != dev.update_state()):
                animate = partial(self.animate, duration=0.1, delay=0.1)
                dev.draw(animate)


    def animate_parties_in(self):
        # TODO: break out functions here for each
        left_trainer, right_trainer = self.players
        right_monster = right_trainer.monsters[0]

        surface = pygame.display.get_surface()
        x, y, w, h = surface.get_rect()

        # TODO: not hardcode this
        player, opponent = self.players
        player_home = self._layout[player]['home'][0]
        opp_home = self._layout[opponent]['home'][0]
        y_mod = scale(50)
        duration = 3

        back_island = self.load_sprite('gfx/ui/combat/' + self.graphics['island_back'],
                                       bottom=opp_home.bottom + y_mod, right=0)

        if self.is_trainer_battle:
            enemy = self.load_sprite('gfx/sprites/player/' + opponent.combat_front,
                                     bottom=back_island.rect.bottom - scale(12),
                                     centerx=back_island.rect.centerx)
            self._monster_sprite_map[opponent] = enemy
        else:
            enemy = right_monster.get_sprite("front",
                                             bottom=back_island.rect.bottom - scale(12),
                                             centerx=back_island.rect.centerx)
            self._monster_sprite_map[right_monster] = enemy
            self.monsters_in_play[opponent].append(right_monster)
            self.build_hud(self._layout[opponent]['hud'][0], right_monster)

        self.sprites.add(enemy)

        if self.is_trainer_battle:
            self.alert(T.format('combat_trainer_appeared', {"name": opponent.name.upper()}))
        else:
            self.alert(T.format('combat_wild_appeared', {"name": right_monster.name.upper()}))

        front_island = self.load_sprite('gfx/ui/combat/' + self.graphics['island_front'],
                                        bottom=player_home.bottom - y_mod, left=w)

        trainer1 = self.load_sprite('gfx/sprites/player/' + player.combat_back,
                                    bottom=front_island.rect.centery + scale(6),
                                    centerx=front_island.rect.centerx)
        self._monster_sprite_map[left_trainer] = trainer1

        def flip():
            enemy.image = pygame.transform.flip(enemy.image, 1, 0)
            trainer1.image = pygame.transform.flip(trainer1.image, 1, 0)

        flip()  # flip images to opposite
        self.task(flip, 1.5)  # flip the images to proper direction

        if not self.is_trainer_battle:  # the combat call is handled by fill_battlefield_positions for trainer battles
            self.task(audio.load_sound(right_monster.combat_call).play, 1.5)  # play combat call when it turns back

        animate = partial(self.animate, transition='out_quad', duration=duration)

        # top trainer
        animate(enemy.rect, back_island.rect, centerx=opp_home.centerx)
        animate(enemy.rect, back_island.rect, y=-y_mod,
                transition='out_back', relative=True)

        # bottom trainer
        animate(trainer1.rect, front_island.rect, centerx=player_home.centerx)
        animate(trainer1.rect, front_island.rect, y=y_mod,
                transition='out_back', relative=True)

    def animate_capture_monster(self, is_captured, num_shakes, monster):
        """ Animation for capturing monsters.

        :param is_captured: boolean representing success of capture
        :param num_shakes: number of shakes before animation ends
        :param monster: the monster
        :return:
        """
        monster_sprite = self._monster_sprite_map.get(monster, None)
        capdev = self.load_sprite('gfx/items/capture_device.png')
        animate = partial(self.animate, capdev.rect, transition='in_quad', duration=1.0)
        graphics.scale_sprite(capdev, .4)
        capdev.rect.center = scale(0), scale(0)
        animate(x=monster_sprite.rect.centerx)
        animate(y=monster_sprite.rect.centery)
        self.task(partial(toggle_visible, monster_sprite), 1.0)  # make the monster go away temporarily

        def kill():
            self._monster_sprite_map[monster].kill()
            self.hud[monster].kill()
            del self._monster_sprite_map[monster]
            del self.hud[monster]

        # TODO: cache this sprite from the first time it's used.
        # also, should loading animated sprites be more convenient?
        images = list()
        for fn in ["capture%02d.png" % i for i in range(1, 10)]:
            fn = 'animations/technique/' + fn
            image = graphics.load_and_scale(fn)
            images.append((image, .07))

        tech = PygAnimation(images, False)
        sprite = Sprite()
        sprite.image = tech
        sprite.rect = tech.get_rect()
        self.task(tech.play, 1.0)
        self.task(partial(self.sprites.add, sprite), 1.0)
        sprite.rect.midbottom = monster_sprite.rect.midbottom

        def shake_ball(initial_delay):
            animate = partial(self.animate, duration=0.1, transition='linear', delay=initial_delay)
            animate(capdev.rect, y=scale(3), relative=True)

            animate = partial(self.animate, duration=0.2, transition='linear', delay=initial_delay + 0.1)
            animate(capdev.rect, y=-scale(6), relative=True)

            animate = partial(self.animate, duration=0.1, transition='linear', delay=initial_delay + 0.3)
            animate(capdev.rect, y=scale(3), relative=True)

        for i in range(0, num_shakes):
            shake_ball(1.8 + i * 1.0)  # leave a 0.6s wait between each shake

        if is_captured:
            self.task(kill, 2 + num_shakes)
        else:
            breakout_delay = 1.8 + num_shakes * 1.0
            self.task(partial(toggle_visible, monster_sprite), breakout_delay)  # make the monster appear again!
            self.task(audio.load_sound(monster.combat_call).play, breakout_delay)
            self.task(tech.play, breakout_delay)
            self.task(capdev.kill, breakout_delay)
