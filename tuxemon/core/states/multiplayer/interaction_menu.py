from core.components.menu import PopUpMenu
from core.components.menu.interface import MenuItem


class InteractionMenu(PopUpMenu):
    def initialize_items(self):
        def duel():
            self.game.wants_duel = True

        def trade():
            pass

        kwagrs = {
            "accept", duel,
            "decline", self.game.pop_state
        }
        kwagrs = {
            "accept", trade,
            "decline", self.game.pop_state
        }

        # if self.game.game.isclient or self.game.game.ishost:
        #    self.game.game.client.player_interact(self.player, "DUEL")
        # self.game.game.client.player_interact(self.player, self.interaction, "CLIENT_RESPONSE", response)


class ConfirmMenu(PopUpMenu):
    def startup(self, **kwargs):
        super(ConfirmMenu, self).startup(**kwargs)
        self.item_to_use = kwargs["item"]

    def calc_final_rect(self):
        rect = self.rect.copy()
        rect.width *= .25
        rect.height *= .3
        rect.center = self.rect.center
        return rect

    def use_selected_item(self):
        item = self.get_selected_item().game_object

        # TODO: combat checks?

        player = self.game.player1
        item.use(player, self.game)

    def initialize_items(self):
        menu_items_map = (
            ('ACCEPT', self.accept),
            ('DECLINE', self.decline),
        )

        for label, callback in menu_items_map:
            image = self.shadow_text(label)
            yield MenuItem(image, label, None, None, callback)
