from __future__ import division

import pygame

from core import prepare
from core import tools
from core.components.menu.menu import Menu
from core.components.menu.interface import HpBar, MenuItem
from core.components.ui.draw import GraphicBox
from core.components.ui.text import draw_text, TextArea


class MonsterMenuState(Menu):
    """ A class to create monster menu objects.

    The monster menu allows you to view monsters in your party,
    teach them moves, and switch them both in and out of combat.
    """
    background_filename = "gfx/ui/monster/monster_menu_bg.png"
    draw_borders = False

    def startup(self, **kwargs):
        super(MonsterMenuState, self).startup(**kwargs)

        # make a text area to show messages
        self.text_area = TextArea(self.font, self.font_color, (96, 96, 96))
        self.text_area.rect = pygame.Rect(tools.scale_sequence([20, 80, 80, 100]))
        self.sprites.add(self.text_area, layer=100)

        # Set up the border images used for the monster slots
        self.monster_slot_border = {}
        self.monster_portrait = pygame.sprite.Sprite()
        self.hp_bar = HpBar()

        # load and scale the monster slot borders
        root = "gfx/ui/monster/"
        border_types = ["empty", "filled", "active"]
        for border_type in border_types:
            filename = root + border_type + "_monster_slot_border.png"
            border = tools.load_and_scale(filename)

            filename = root + border_type + "_monster_slot_bg.png"
            background = tools.load_image(filename)

            window = GraphicBox(border, background, None)
            self.monster_slot_border[border_type] = window

        # TODO: something better than this global, load_sprites stuff
        for monster in self.game.player1.monsters:
            monster.load_sprites()

    def animate_monster_down(self):
        ani = self.animate(self.monster_portrait.rect, y=-tools.scale(5),
                           duration=1, transition='in_out_quad', relative=True)
        ani.callback = self.animate_monster_up

    def animate_monster_up(self):
        ani = self.animate(self.monster_portrait.rect, y=tools.scale(5),
                           duration=1, transition='in_out_quad', relative=True)
        ani.callback = self.animate_monster_down

    def calc_menu_items_rect(self):
        width, height = self.rect.size
        left = width // 2.25
        top = height // 12
        width /= 2
        return pygame.Rect(left, top, width, height - top * 2)

    def initialize_items(self):
        # position the monster portrait
        try:
            monster = self.game.player1.monsters[self.selected_index]
            image = monster.sprites["front"]
        except IndexError:
            image = pygame.Surface((1, 1), pygame.SRCALPHA)

        # position and animate the monster portrait
        width, height = prepare.SCREEN_SIZE
        self.monster_portrait.rect = image.get_rect(centerx=width // 4, top=height // 12)
        self.sprites.add(self.monster_portrait)
        self.animations.empty()
        self.animate_monster_down()

        width = prepare.SCREEN_SIZE[0] // 2
        height = prepare.SCREEN_SIZE[1] // (self.game.player1.party_limit * 1.5)

        # make 6 slots
        for i in range(self.game.player1.party_limit):
            rect = pygame.Rect(0, 0, width, height)
            surface = pygame.Surface(rect.size, pygame.SRCALPHA)
            item = MenuItem(surface, None, None, None)
            yield item

        self.refresh_menu_items()

    def on_menu_selection(self, menu_item):
        pass

    def render_monster_slot(self, surface, rect, monster, in_focus):
        filled = monster is not None
        border = self.determine_border(in_focus, filled)
        border.draw(surface)
        if filled:
            self.draw_monster_info(surface, monster, rect)
        return surface

    def refresh_menu_items(self):
        """ Used to render slots after their 'focus' flags change

        :return:
        """
        for index, item in enumerate(self.menu_items):
            try:
                monster = self.game.player1.monsters[index]
            except IndexError:
                monster = None
            item.game_object = monster
            item.enabled = monster is not None
            item.image.fill((0, 0, 0, 0))
            # TODO: Cleanup this hack
            if index == self.selected_index:
                item.in_focus = True
            self.render_monster_slot(item.image, item.image.get_rect(), item.game_object, item.in_focus)

    def draw_monster_info(self, surface, monster, rect):
        # position and draw hp bar
        hp_rect = rect.copy()
        left = rect.width * .6
        right = rect.right - tools.scale(4)
        hp_rect.width = right - left
        hp_rect.left = left
        hp_rect.height = tools.scale(8)
        hp_rect.centery = rect.centery

        # draw the hp bar
        self.hp_bar.value = monster.current_hp / monster.hp
        self.hp_bar.draw(surface, hp_rect)

        # draw the name
        text_rect = rect.inflate(-tools.scale(6), -tools.scale(6))
        draw_text(surface, monster.name, text_rect, font=self.font)

        # draw the level info
        text_rect.top = rect.bottom - tools.scale(7)
        draw_text(surface, "  Lv " + str(monster.level), text_rect, font=self.font)

        # draw any status icons
        # TODO: caching or something, idk
        # TODO: not hardcode icon sizes
        for index, status in enumerate(monster.status):
            if status.icon:
                image = tools.load_and_scale(status.icon)
                pos = (rect.width * .4) + (index * tools.scale(32)), rect.y + tools.scale(5)
                surface.blit(image, pos)

    def determine_border(self, selected, filled):
        if selected:
            return self.monster_slot_border['active']
        elif filled:
            return self.monster_slot_border['filled']
        else:
            return self.monster_slot_border['empty']

    def on_menu_selection_change(self):
        try:
            monster = self.game.player1.monsters[self.selected_index]
            image = monster.sprites["front"]
        except IndexError:
            image = pygame.Surface((1, 1), pygame.SRCALPHA)
        self.monster_portrait.image = image
        self.refresh_menu_items()
