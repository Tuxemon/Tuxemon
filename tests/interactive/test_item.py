"""
from item.py
"""

if __name__ == "__main__":
    pygame.init()

    # set up the window
    screen = pygame.display.set_mode((800, 600), 1, 32)

    potion_item = Item("Potion")
    pprint.pprint(potion_item.__dict__)
