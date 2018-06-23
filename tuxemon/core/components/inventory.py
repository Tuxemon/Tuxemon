from tuxemon.core.components.item import Item

class Inventory(object):
    """an inventory ( that contain item )"""
    def __init__(self):
        self.inventory = {}

    def create_item_place(self, slug):
        """create a emply place for item named slug in the player inventory ( only if needed )"""
        if not slug in self.inventory:
            self.inventory[slug] = {'item' : Item(slug),
            'quantity' : 0}
            return True
        else:
            return False

    def add_item(self, item, quantity=1):
        """add an item in the inventory
        item : the Item object"""
        # If the item already exists in the player's inventory, add to its quantity, otherwise
        # just add the item.
        self.create_item_place(item.slug)
        self.inventory[item.slug]['quantity'] += quantity

    def add_item_slug(self, slug, quantity=1):
        """add an item in the inventory based on his slug"""
        item_to_add = Item(slug)
        self.add_item(item_to_add, quantity=quantity)

    def get(self, slug):
        return self.inventory.get(slug)

    def get_all(self):
        return self.inventory

    def delete_item_slug(self, slug, quantity=1):
        quantity_in_inventory = self.get_item_number_slug(slug)
        self.get(slug)["quantity"] -= quantity
        # delete item if 0 or less
        if self.get_item_number_slug(slug) <= 0:
            del self.inventory[slug]

    def get_item_number_slug(self, slug):
        return self.inventory[slug]["quantity"]
