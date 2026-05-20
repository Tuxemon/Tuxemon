"""Static game constants for colors, asset paths, and font sizes."""

# Asset Paths
GFX_HP_BAR: str = "gfx/ui/monster/hp_bar.png"
GFX_XP_BAR: str = "gfx/ui/monster/exp_bar.png"
MISSING_IMAGE: str = "gfx/sprites/battle/missing.png"

# Colors (RGB tuples)
HP_COLOR_FG = (10, 240, 25)  # dark saturated green
HP_COLOR_BG = (245, 10, 25)  # dark saturated red
XP_COLOR_FG = (31, 239, 255)  # light washed cyan
XP_COLOR_BG = None

BLACK_COLOR = (0, 0, 0)
WHITE_COLOR = (255, 255, 255)
RED_COLOR = (255, 0, 0)
GREEN_COLOR = (0, 255, 0)
FUCHSIA_COLOR = (255, 0, 255)
SEA_BLUE_COLOR = (0, 105, 148)
DARKGRAY_COLOR = (169, 169, 169)
DIMGRAY_COLOR = (105, 105, 105)
UNAVAILABLE_COLOR = (220, 220, 220)
UNAVAILABLE_COLOR_SHOP = (51, 51, 51)
TRANSPARENT_COLOR = (255, 255, 255, 0)
BACKGROUND_COLOR = (248, 248, 248)  # Guyabano
FONT_COLOR = BLACK_COLOR
FONT_SHADOW_COLOR = (192, 192, 192)  # silver
SCROLLBAR_COLOR = (237, 246, 248)
SCROLLBAR_SLIDER_COLOR = (197, 232, 234)

# Gradient Paths
GRAD_BLACK: str = "gfx/ui/background/gradient_black.png"
GRAD_BLUE: str = "gfx/ui/background/gradient_blue.png"
GRAD_BROWN: str = "gfx/ui/background/gradient_brown.png"
GRAD_GREEN: str = "gfx/ui/background/gradient_green.png"
GRAD_ORANGE: str = "gfx/ui/background/gradient_orange.png"
GRAD_RED: str = "gfx/ui/background/gradient_red.png"
GRAD_VIOLET: str = "gfx/ui/background/gradient_violet.png"
GRAD_YELLOW: str = "gfx/ui/background/gradient_yellow.png"

# Background Paths
TUX_GENERIC: str = "gfx/ui/background/tux_generic.png"
TUX_CHOICE: str = "gfx/ui/background/tux_choice.png"
TUX_INFO: str = "gfx/ui/background/tux_info.png"
TECH_INFO: str = "gfx/ui/background/tech_info.png"
ITEM_MENU: str = "gfx/ui/item/item_menu_bg.png"
INDIV_INFO: str = "gfx/ui/background/passportbackground.png"
PYGAME_LOGO: str = "gfx/ui/intro/pygame_logo.png"
CREATIVE_COMMONS: str = "gfx/ui/intro/creative_commons.png"
BG_PLAYER1: str = "gfx/ui/background/player_info.png"
BG_PLAYER2: str = "gfx/ui/background/player_info1.png"
BG_PARTY: str = "gfx/ui/background/player_info2.png"
BG_ITEMS_BACKPACK: str = "gfx/ui/item/backpack.png"
BG_MONSTERS: str = "gfx/ui/monster/monster_menu_bg.png"

# Background paths per state (using gradients)
BG_MINIGAME: str = GRAD_BLUE
BG_MISSIONS: str = GRAD_BLUE
BG_PC_KENNEL: str = GRAD_BLUE
BG_PC_LOCKER: str = GRAD_BLUE
BG_PHONE: str = GRAD_BLUE
BG_PHONE_BANKING: str = GRAD_BLUE
BG_PHONE_CONTACTS: str = GRAD_BLUE
BG_PHONE_MAP: str = GRAD_BLUE
BG_PHONE_RENAMING: str = GRAD_BLUE
BG_START_SCREEN: str = GRAD_BLUE
BG_JOURNAL: str = TUX_GENERIC
BG_JOURNAL_CHOICE: str = TUX_CHOICE
BG_JOURNAL_INFO: str = TUX_INFO
BG_MONSTER_INFO: str = TUX_INFO
BG_ITEMS: str = ITEM_MENU
BG_MOVES: str = ITEM_MENU

# Font Sizes
# Note: These values are relative size indices, not pixel counts.
FONT_SIZE_SMALLER = 3
FONT_SIZE_SMALL = 4
FONT_SIZE = 5
FONT_SIZE_BIG = 6
FONT_SIZE_BIGGER = 7
FONT_SIZE_BIGGEST = 8
