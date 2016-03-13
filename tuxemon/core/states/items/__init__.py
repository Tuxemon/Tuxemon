from __future__ import division

from core import tools
from core.components.menu.interface import MenuItem
from core.components.menu.menu import Menu, PopUpMenu
from core.components.sprite import Sprite
from core.components.ui.text import TextArea


class UseItemConfirmMenuState(PopUpMenu):
    shrink_to_items = True

    def initialize_items(self):
        menu_items = ('USE', 'CANCEL')
        for label in menu_items:
            image = self.shadow_text(label)
            yield MenuItem(image, label, None, None)


class ItemMenuState(Menu):
    """A class to create item menu objects. The item menu allows you to view and use items in your
    inventory.
    """
    background_filename = "gfx/ui/item/item_menu_bg.png"
    draw_borders = False

    def startup(self, **kwargs):
        self.state = "normal"
        self.item_center = self.rect.width * .164, self.rect.height * .13
        self.item_sprite = Sprite()
        self.item_sprite.image = None
        self.sprites.add(self.item_sprite)
        super(ItemMenuState, self).startup(**kwargs)
        self.menu_items.line_spacing = tools.scale(5)

        rect = self.game.screen.get_rect()
        center = rect.center
        rect.width *= .95
        rect.height *= .25
        rect.center = center
        rect.top = tools.scale(110)
        self.text_area = TextArea(self.font, self.font_color, (96, 96, 128))
        self.text_area.rect = rect
        self.sprites.add(self.text_area, layer=100)

        # Load the backpack icon
        self.backpack_center = self.rect.width * .16, self.rect.height * .45
        self.load_sprite("gfx/ui/item/backpack.png", center=self.backpack_center, layer=100)

    def calc_internal_rect(self):
        rect = self.rect.copy()
        rect.width *= .58
        rect.left = self.rect.width * .365
        rect.top = rect.height * .05
        rect.height = self.rect.height * .60
        return rect

    def determine_state_called_from(self):
        # hackish way to just get this working...  may come back to this later, idk
        return self.game.active_states[-1].name

    def on_menu_selection(self, menuitem):
        def use_item(menuitem):
            player = self.game.player1
            monster = menuitem.game_object
            self.game.pop_state()  # close the monster menu

            if state == "CombatState":
                self.game.get_state_name("CombatState").enqueue_action(player, item, player.monsters[0])
                self.game.pop_state()   # pop this menu
            else:
                item.use(player, monster)
                self._initialize_items()  # re-init, in case one item is gone now

        def decide_to_use(menuitem):
            self.game.pop_state()  # close the confirm dialog
            if menuitem.label == "USE":
                self.game.push_state("MonsterMenuState", on_menu_selection=use_item)

        item = menuitem.game_object
        state = self.determine_state_called_from()
        if state in item.usable_in:
            self.game.push_state("UseItemConfirmMenuState", on_menu_selection=decide_to_use)
        else:
            rect = self.game.screen.get_rect()
            center = rect.center
            rect.height /= 6
            rect.width *= .8
            rect.center = center
            tools.open_dialog(self.game, ["%s cannot be used here!" % item.name])

    def initialize_items(self):
        """ get all player items and update the items in the list
        """
        for name, properties in self.game.player1.inventory.items():
            obj = properties['item']
            image = self.shadow_text(obj.name, bg=(128, 128, 128))
            yield MenuItem(image, obj.name, obj.description, obj)

    def on_menu_selection_change(self):
        self.update_item_sprite()
        item = self.get_selected_item()
        if item:
            self.alert(item.description)

    def update_item_sprite(self):
        item = self.get_selected_item()
        if item:
            image = item.game_object.surface
            self.item_sprite.image = image
            self.item_sprite.rect = image.get_rect(center=self.backpack_center)

            # animate item being pulled from the bag
            self.animate(self.item_sprite.rect, centery=self.item_center[1], duration=.2)
