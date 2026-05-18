"""Static game constants for sizes, limits, and multipliers."""

UNKNOWN_MAP_SLUG: str = "unknown_map"

# Map / Region Keys
REGION_KEYS: list[str] = [
    "enter_from",
    "exit_from",
    "endure",
    "key",
    "push_direction",
    "push_strength",
    "speed_modifier",
]
# Surface Keys (tilesets)
SURFACE_KEYS: list[str] = ["surfable", "walkable", "climbable"]

MONTH_KEYS = [
    "month_jan",
    "month_feb",
    "month_mar",
    "month_apr",
    "month_may",
    "month_jun",
    "month_jul",
    "month_aug",
    "month_sep",
    "month_oct",
    "month_nov",
    "month_dec",
]

MAP_CACHE_SIZE: int = 10
PLAYER_NPC = "npc_red"

# Asset Sizes (Native)
TILE_SIZE: tuple[int, int] = (16, 16)  # 1 tile = 16 pixels
ICON_SIZE: tuple[int, int] = (7, 7)
TECH_ICON_SIZE: tuple[int, int] = (9, 9)
STATUS_ICON_SIZE: tuple[int, int] = (9, 9)
SPRITE_SIZE: tuple[int, int] = (16, 32)
ITEM_SIZE: tuple[int, int] = (24, 24)
TEMPLATE_SIZE: tuple[int, int] = (64, 64)
MONSTER_SIZE: tuple[int, int] = (64, 64)
MONSTER_SIZE_MENU: tuple[int, int] = (24, 24)
BORDERS_SIZE: tuple[int, int] = (18, 18)
ELEMENT_SIZE: tuple[int, int] = (24, 24)
BATTLE_BG_SIZE: tuple[int, int] = (256, 108)

# Native resolution is similar to the old gameboy resolution.
NATIVE_RESOLUTION: tuple[int, int] = (256, 144)

# Conversion Factors
COEFF_TILE: float = 1.0
COEFF_MILES: float = 0.6213711922
COEFF_FEET: float = 0.032808399
COEFF_POUNDS: float = 2.2046

# Player / Party Limits
PLAYER_NAME_LIMIT: int = 15
PARTY_LIMIT: int = 6
MOVERATE_RANGE: tuple[float, float] = (0.0, 20.0)
TRANS_TIME: float = 0.3

# PC Limits
KENNEL: str = "Kennel"
LOCKER: str = "Locker"
MAX_KENNEL: int = 30
MAX_LOCKER: int = 30
MUSIC_RANGE: tuple[float, float] = (0.0, 1.0)
SOUND_RANGE: tuple[float, float] = (0.0, 1.0)
MUSIC_LOOP: int = -1
MUSIC_FADEIN: int = 1000
MUSIC_FADEOUT: int = 1000

U_KM: str = "km"
U_MI: str = "mi"
U_KG: str = "kg"
U_T: str = "t"
U_M: str = "m"
U_LB: str = "lb"
U_CM: str = "cm"
U_FT: str = "ft"

# Item Limits
MAX_TYPES_BAG: int = 99
MAX_MENU_ITEMS: int = 11

# Camera
CAMERA_SHAKE_RANGE: tuple[float, float] = (0.0, 3.0)

# Techniques
RECHARGE_RANGE: tuple[int, int] = (0, 5)
POTENCY_RANGE: tuple[float, float] = (0.0, 1.0)
ACCURACY_RANGE: tuple[float, float] = (0.0, 1.0)
POWER_RANGE: tuple[float, float] = (0.0, 3.0)
HEALING_POWER_RANGE: tuple[float, float] = (0.0, 3.0)

# Combat
MONSTERS_DOUBLE: int = 3
COEFF_DAMAGE: int = 7  # Coefficient for damage calculation
