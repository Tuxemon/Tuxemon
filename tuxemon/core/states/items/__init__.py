from tuxemon.core import tools
from tuxemon.core.locale import T
from tuxemon.core.menu.interface import MenuItem
from tuxemon.core.menu.menu import Menu
from tuxemon.core.menu.quantity import QuantityMenu
from tuxemon.core.session import local_session
from tuxemon.core.sprite import Sprite
from tuxemon.core.ui.text import TextArea

# The import is required for PushState to work.
# But linters may say the import is unused.
assert QuantityMenu


class ItemMenuState(Menu):
    """ The item menu allows you to view and use items in your inventory.
    """
    background_filename = "gfx/ui/item/item_menu_bg.png"
    draw_borders = False

    def startup(self, **kwargs):
        self.state = "normal"

        # this sprite is used to display the item
        # its also animated to pop out of the backpack
        self.item_center = self.rect.width * .164, self.rect.height * .13
        self.item_sprite = Sprite()
        self.item_sprite.image = None
        self.sprites.add(self.item_sprite)

        # do not move this line
        super().startup(**kwargs)
        self.menu_items.line_spacing = tools.scale(7)

        # this is the area where the item description is displayed
        rect = self.client.screen.get_rect()
        rect.top = tools.scale(106)
        rect.left = tools.scale(3)
        rect.width = tools.scale(250)
        rect.height = tools.scale(32)
        self.text_area = TextArea(self.font, self.font_color, (96, 96, 128))
        self.text_area.rect = rect
        self.sprites.add(self.text_area, layer=100)

        # load the backpack icon
        self.backpack_center = self.rect.width * .16, self.rect.height * .45
        self.load_sprite("gfx/ui/item/backpack.png", center=self.backpack_center, layer=100)

    def calc_internal_rect(self):
        # area in the screen where the item list is
        rect = self.rect.copy()
        rect.width *= .58
        rect.left = self.rect.width * .365
        rect.top = rect.height * .05
        rect.height = self.rect.height * .60
        return rect

    def determine_state_called_from(self):
        dex = self.client.active_states.index(self)
        return self.client.active_states[dex + 1].name

    def on_menu_selection(self, menu_item):
        """ Called when player has selected something from the inventory

        Currently, opens a new menu depending on the state context

        :param menu_item:
        :return:
        """
        item = menu_item.game_object
        state = self.determine_state_called_from()

        if not any(menu_item.game_object.validate(m) for m in local_session.player.monsters):
            msg = T.format('item_no_available_target', {'name': item.name})
            tools.open_dialog(local_session, [msg])
        elif state not in item.usable_in:
            msg = T.format('item_cannot_use_here', {'name': item.name})
            tools.open_dialog(local_session, [msg])
        else:
            self.open_confirm_use_menu(item)

    def open_confirm_use_menu(self, item):
        """ Confirm if player wants to use this item, or not

        :return: None
        """

        def use_item(menu_item):
            player = local_session.player
            monster = menu_item.game_object

            # item must be used before state is popped.
            result = item.use(player, monster)
            self.client.pop_state()  # pop the monster screen
            self.client.pop_state()  # pop the item screen
            tools.show_item_result_as_dialog(local_session, item, result)

        def confirm():
            self.client.pop_state()  # close the confirm dialog
            # TODO: allow items to be used on player or "in general"

            menu = self.client.push_state("MonsterMenuState")
            menu.is_valid_entry = item.validate
            menu.on_menu_selection = use_item

        def cancel():
            self.client.pop_state()  # close the use/cancel menu

        def open_choice_menu():
            # open the menu for use/cancel
            menu = self.client.push_state("Menu")
            menu.shrink_to_items = True

            menu_items_map = (
                ('item_confirm_use', confirm),
                ('item_confirm_cancel', cancel)
            )

            # add our options to the menu
            for key, callback in menu_items_map:
                label = T.translate(key).upper()
                image = self.shadow_text(label)
                item = MenuItem(image, label, None, callback)
                menu.add(item)

        open_choice_menu()

    def sort_inventory(self, inventory):
        """ Sort inventory in a usable way.  Expects a list of inventory properties.
        
        * Group items by category
        * Sort in groups by name
        * Group order: Potions, Food, Utility Items, Quest/Game Items
        
        :return: Sorted copy of the inventory
        """

        def rank_item(properties):
            item = properties['item']
            primary_order = sort_order.index(item.sort)
            return primary_order, item.name

        # the two reversals are used to let name sort desc, but class sort asc
        sort_order = ['potion', 'food', 'utility', 'quest']
        sort_order.reverse()
        return sorted(inventory, key=rank_item, reverse=True)

    def initialize_items(self):
        """ Get all player inventory items and add them to menu

        :return:
        """
        inventory = local_session.player.inventory.values()

        # required because the max() below will fail if inv empty
        if not inventory:
            return

        name_len = 17  # TODO: dynamically get this value, maybe?
        count_len = max(len(str(p['quantity'])) for p in inventory)

        # TODO: move this and other format strings to a locale or config file
        label_format = "{:<{name_len}} x {:>{count_len}}".format

        for properties in self.sort_inventory(inventory):
            obj = properties['item']
            formatted_name = label_format(obj.name, properties['quantity'],
                                          name_len=name_len, count_len=count_len)
            image = self.shadow_text(formatted_name, bg=(128, 128, 128))
            yield MenuItem(image, obj.name, obj.description, obj)

    def on_menu_selection_change(self):
        """ Called when menu selection changes

        :return: None
        """
        item = self.get_selected_item()
        if item:
            # animate item being pulled from the bag
            image = item.game_object.surface
            self.item_sprite.image = image
            self.item_sprite.rect = image.get_rect(center=self.backpack_center)
            self.animate(self.item_sprite.rect, centery=self.item_center[1], duration=.2)

            # show item description
            self.alert(item.description)


class ShopMenuState(Menu):
    background_filename = "gfx/ui/item/item_menu_bg.png"
    draw_borders = False

    def startup(self, **kwargs):
        self.state = "normal"

        # this sprite is used to display the item
        self.item_center = self.rect.width * .164, self.rect.height * .13
        self.item_sprite = Sprite()
        self.item_sprite.image = None
        self.sprites.add(self.item_sprite)

        # do not move this line
        super().startup(**kwargs)
        self.menu_items.line_spacing = tools.scale(7)

        # this is the area where the item description is displayed
        rect = self.client.screen.get_rect()
        rect.top = tools.scale(106)
        rect.left = tools.scale(3)
        rect.width = tools.scale(250)
        rect.height = tools.scale(32)
        self.text_area = TextArea(self.font, self.font_color, (96, 96, 128))
        self.text_area.rect = rect
        self.sprites.add(self.text_area, layer=100)

        self.image_center = self.rect.width * .16, self.rect.height * .45
        self.buyer = kwargs["buyer"]
        self.seller = kwargs["seller"]
        self.buyer_purge = kwargs.get("buyer_purge", False)

    def calc_internal_rect(self):
        # area in the screen where the item list is
        rect = self.rect.copy()
        rect.width *= .58
        rect.left = self.rect.width * .365
        rect.top = rect.height * .05
        rect.height = self.rect.height * .60
        return rect

    def on_menu_selection(self, menu_item):
        """ Called when player has selected something from the inventory

        Currently, opens a new menu depending on the state context

        :param menu_item:
        :return:
        """
        item = menu_item.game_object

        def use_item(quantity):
            if not quantity:
                return

            if self.buyer:
                self.seller.give_item(self.client, self.buyer, item, quantity)
            else:
                self.seller.alter_item_quantity(self.client, item.slug, -quantity)
            self.reload_items()
            if not self.seller.has_item(item.slug):
                # We're pointing at a new item
                self.on_menu_selection_change()

        item_dict = self.seller.inventory[item.slug]
        max_quantity = None if item_dict.get("infinite") else item_dict['quantity']
        self.client.push_state(
            "QuantityMenu",
            callback=use_item,
            max_quantity=max_quantity,
            quantity=1,
            shrink_to_items=True,
        )

    def sort_inventory(self, inventory):
        """ Sort inventory in a usable way.  Expects a list of inventory properties.

        * Group items by category
        * Sort in groups by name
        * Group order: Potions, Food, Utility Items, Quest/Game Items

        :return: Sorted copy of the inventory
        """

        def rank_item(properties):
            item = properties['item']
            primary_order = sort_order.index(item.sort)
            return primary_order, item.name

        # the two reversals are used to let name sort desc, but class sort ascending
        sort_order = ['potion', 'food', 'utility', 'quest']
        sort_order.reverse()
        return sorted(inventory, key=rank_item, reverse=True)

    def initialize_items(self):
        """ Get all player inventory items and add them to menu

        :return:
        """
        inventory = [
            item
            for item in self.seller.inventory.values()
            if not (self.seller.isplayer and item['item'].sort == "quest")
        ]

        # required because the max() below will fail if inv empty
        if not inventory:
            return

        name_len = 17  # TODO: dynamically get this value, maybe?
        count_len = max(len(str(p['quantity'])) for p in inventory)

        # TODO: move this and other format strings to a locale or config file
        label_format_1 = "{:<{name_len}} x {:>{count_len}}".format
        label_format_2 = "{:<{name_len}}".format

        for properties in self.sort_inventory(inventory):
            obj = properties['item']
            if properties.get('infinite'):
                label = label_format_2
            else:
                label = label_format_1
            formatted_name = label(obj.name, properties['quantity'],
                                   name_len=name_len, count_len=count_len)
            image = self.shadow_text(formatted_name, bg=(128, 128, 128))
            yield MenuItem(image, obj.name, obj.description, obj)

    def on_menu_selection_change(self):
        """ Called when menu selection changes

        :return: None
        """
        item = self.get_selected_item()
        if item:
            image = item.game_object.surface
            self.item_sprite.image = image
            self.item_sprite.rect = image.get_rect(center=self.image_center)
            self.alert(item.description)
