"""Generate the menu-driven Ladder campaign from the table below.

Run from the repo root:  .venv/bin/python scripts/ladder/gen.py

Writes (overwrites) these files; edit the tables here and in world.py (the
routes), not the outputs:
  mods/tuxemon/maps/ladder_hub.yaml         hub, route and gym menus
  mods/tuxemon/db/encounter/ladder_route_N_<area>.yaml
  mods/tuxemon/db/npc/ladder_people.yaml    one NPC per gym trainer
  mods/tuxemon/l18n/en_US/LC_MESSAGES/base.po  (block between the markers)
check_world.py checks the tables and these files.

How it plays: six towns (TOWNS; town N has route N and gym N). Main menu >
Map > a route's areas or a town's four temples. A route area is one wild
encounter; a gym is "Fight the next trainer / Leave", trainers in order,
leader last. Beating gym N's leader or satisfying any townsperson
(researcher, collector, breeder) opens the next town; the others stay as
soft rewards. Town 6 is the summit: there each path satisfied is that path's
ending (ENDINGS). The campaign sets rule_heal_after_battle, so the team is
fully healed after every battle (tuxemon/combat/utils.py).
"""

import re
import sys
from pathlib import Path

import yaml

# Requests come in two scales (Stephen, 2026-11-25): (easy, real). The game is
# generated with the easy ones while the campaign's shape is tried out.
EASY = True

STARTERS = ["agnite", "squink", "budaye"]  # fire, water, wood
STARTER_LEVEL = 5
KITS = 50  # tuxeballs given at the start

# Routes: the table in world.py (every species in exactly one area; first
# written by place_world.py, edited by hand since). Route N comes before gym N
# and offers counters to gym N's type; each area has its own terrain, mix of
# monsters (weights = relative chance; the last is the rare one) and a hint.
sys.path.insert(0, str(Path(__file__).parent))
from world import ROUTES  # noqa: E402


# What the dialog box shows (measured 2026-11-25, see the report): the game's
# font is monospaced, 25 px a character at 1280x720; a line of the real game
# holds 37 characters (proved by the owner's screenshot: a 37-character line
# fits, a 41-character one wraps) and the box shows 4 lines (the fifth is cut
# off). Both are deliberately the lower bounds of what was seen. The game never
# pages a text by itself except at a newline. This is the one place that knows
# the budget; build() splits every dialog text that is over it into pages.
COLS, ROWS = 37, 4
PAGE_BREAK = "\f"  # inside a text: a page boundary the author wants


def fits(text, bounds=None):
    """True if `text` (placeholders at their longest) wraps into at most ROWS lines of COLS characters."""
    return len(wrap(substitute(text, bounds))) <= ROWS


def wrap(text):
    """The lines the game's word wrap makes of `text`: words kept whole, a line at most COLS characters."""
    lines, line = [], ""
    for word in text.split():
        if len(word) > COLS:
            raise SystemExit(f"a single word is wider than the dialog box ({COLS} characters): {word!r}")
        if line and len(line) + 1 + len(word) > COLS:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    return lines + ([line] if line else [])


def req(value):
    """The easy or the real value of a request given as (easy, real)."""
    if isinstance(value, tuple):
        return value[0] if EASY else value[1]
    return value


def route_monsters(route):
    """Every species found anywhere on the route, in area order."""
    out = []
    for area in route["areas"]:
        out += [m for m in area["monsters"] if m not in out]
    return out

# Each gym's "name" is its flavour name (placeholders, Stephen may change them):
# the title of the gym's menu, the only place the player reads it.
# Each trainer: (sprite, title, [(monster, level), ...]); the last one is the leader.
GYMS = [
    {
        "name": "Hartwood",
        "trainers": [
            # Easy on purpose (Stephen, 2026-11-25): one low-level monster each,
            # so every battle can be won; difficulty gets tuned later.
            ("picnicker", "Picnicker Ada", [("anoleaf", 2)]),
            ("tennisplayer", "Tennis player Bo", [("conileaf", 2)]),
            ("scientist", "Botanist Cy", [("fordin", 3)]),
            ("monk", "Leader Sylva", [("lambert", 4)]),
        ],
    },
    {
        "name": "Tidewell",
        "trainers": [
            ("swimmer", "Swimmer Dee", [("kroki", 3)]),
            ("fisher", "Fisher Eli", [("jelillow", 3)]),
            ("beachcomber", "Beachcomber Fen", [("nostray", 4)]),
            ("riverboatcaptain", "Leader Marina", [("pharfan", 5)]),
        ],
    },
    # Gyms 3-6 the same way: one monster each, levels N+1, N+1, N+2, N+3.
    {
        "name": "Stonehold",
        "trainers": [
            ("miner", "Miner Gus", [("rockat", 4)]),
            ("soldier", "Soldier Hal", [("rooksand", 4)]),
            ("rogue", "Digger Ike", [("vividactil", 5)]),
            ("warrior", "Leader Terra", [("regalance", 6)]),
        ],
    },
    {
        "name": "Cinderhall",
        "trainers": [
            ("firefighter", "Firefighter Jo", [("foxfire", 5)]),
            ("firenymph", "Nymph Kai", [("knindling", 5)]),
            ("cooldude", "Smith Lu", [("cobarett", 6)]),
            ("dragonrider", "Leader Blaze", [("vulpyre", 7)]),
        ],
    },
    {
        "name": "Steelhearth",
        "trainers": [
            ("robot", "Robot Max", [("botbot", 6)]),
            ("xerogrunt", "Grunt Nia", [("nut", 6)]),
            ("scientist", "Engineer Oz", [("sprorm", 7)]),
            ("knightlord", "Leader Ferro", [("tigrock", 8)]),
        ],
    },
    # The summit: the final tier of the warrior's path. The leader is the
    # boss, six monsters (one of each gym's type and a cosmic one), all level
    # 6 for now (Stephen, 2026-11-25: no difficulty tuning yet).
    {
        "name": "Starreach",
        "trainers": [
            ("magician", "Magician Pax", [("flummby", 7)]),
            ("witch", "Witch Qi", [("eyesore", 7)]),
            ("professor", "Professor Ren", [("forturtle", 8)]),
            ("overseer", "Master Zenith", [("flummack", 6), ("chloragon", 6), ("shnark", 6),
                                         ("vividactil", 6), ("ruption", 6), ("wrougon", 6)]),
        ],
    },
]

# gym N's type, for the researcher's tip (gym 6 is the summit; its trainers
# are cosmic and its boss has one of each)
GYM_TYPES = ["wood", "water", "earth", "fire", "metal", "cosmic"]

# Townspeople of town 1. Satisfying any one of them (or the gym leader) opens
# the next town; the rest are soft rewards that invite other play styles.
# Rewards: key -> (menu label, actions). {tip} is the researcher's gym tip.
REWARDS = {
    "kits_10": ("10 Tuxeballs", ["add_item tuxeball,10"]),
    "kits_20": ("20 Tuxeballs", ["add_item tuxeball,20"]),
    "tm_frostbite": ("Move disc: Frostbite", ["add_item tm_frostbite,1"]),
    **{f"tip_{kind}_{n}": (f"A tip about {'the warrior temple' if kind == 'gym' else f'Route {n}'}", [f"translated_dialog ladder_tip_{kind}_{n}"])
       for n in range(1, 7) for kind in ("gym", "route")},
    "gift_eskipup": ("An Eskipup (level 8)", ["add_monster eskipup,8", "translated_dialog ladder_got_eskipup"]),
    "gift_pipis": ("A Pipis (level 10)", ["add_monster pipis,10", "translated_dialog ladder_got_pipis"]),
}
# Rewards point AWAY from the person's own style, so each one nudges the
# player toward another way of playing (decided 2026-11-24): the researcher
# gives no information, the collector no monsters or tuxeballs, the breeder no
# experience.
# Every request is (easy, real); see EASY and req().
RESEARCHER = {"seen": (5, 5), "rewards": ["kits_10", "gift_eskipup", "tm_frostbite"]}
COLLECTOR = {"species": (3, 3), "rewards": ["tip_gym_1", "tip_route_1", "tm_frostbite"]}
BREEDER = {
    # goal = (easy, real): one level for now, since wild monsters are level
    # 1-2 and give little experience (2026-11-25).
    "monster": "lapinou", "name": "Billy", "start": 5, "goal": (6, 10),
    "keep_rewards": ["kits_10", "tip_gym_1", "tm_frostbite"],  # show Billy, keep Billy
    "give_rewards": ["gift_pipis", "kits_20", "gift_eskipup"],  # give Billy back
}

# The four paths and the ranks their temples give (placeholder titles,
# 2026-11-25), one per town. The rank rises once per town, when that town's
# townsperson is satisfied (the gym leader beaten, for the warrior): it becomes
# the town's number unless it is already higher. Pupils' bets give no rank.
# Town N's pupils carry title N, so the top title comes only from the final
# temple.
PATHS = {
    "warrior": ["Initiate", "Squire", "Knight", "Captain", "Paladin", "Champion"],
    "scholar": ["Novice", "Scribe", "Sage", "Archivist", "Luminary", "Loremaster"],
    "seeker": ["Wanderer", "Scout", "Pathfinder", "Ranger", "Voyager", "Trailblazer"],
    "keeper": ["Stablehand", "Herder", "Warden", "Shepherd", "Steward", "Guardian"],
}


def rank_up(path, town):
    """Actions for satisfying `path` in `town`: raise the rank to the town's, announce it."""
    return [f"rank_up {path},{':'.join(PATHS[path])},{town}", f"translated_dialog ladder_rank_up_{path}"]


# Temples are walked in order (Stephen, 2026-11-25): path P's temple in town N
# opens only when P's temple is finished in towns 1..N-1. Finished = the town's
# townsperson satisfied, or the gym's leader beaten (the conditions that open
# the next town and raise the rank).
JOBS = {"scholar": "researcher", "seeker": "collector", "keeper": "breeder"}


def finished(path, t):
    """The condition 'path's temple in town t is finished'."""
    if path == "warrior":
        return f"is battle_outcome player,won,{trainer_slug(t, len(GYMS[t - 1]['trainers']))}"
    return f"is variable_set ladder_{JOBS[path]}{town_suffix(t)}:done"


def open_conds(path, tn):
    """Conditions for entering path's temple in town tn: every earlier town's temple is finished."""
    return [finished(path, t) for t in range(1, tn)]


def closed_door(events, strings, key, pick, speaker, path, tn):
    """The refusals at a temple's door: one per first unfinished town k < tn.

    `speaker` says it (the pupil, or the gym's first trainer), then the town's
    menu returns. The player's title on the path is the one of town k-1 (none
    for k = 1). `pick` is the pick variable:value that enters the temple.
    """
    for k in range(1, tn):
        town = TOWNS[k - 1]["name"]
        if k == 1:
            now = f"You have not set foot on the {path}'s path."
        else:
            title = PATHS[path][k - 2]
            now = f"You're just {'an' if title[0] in 'AEIOU' else 'a'} {title}."
        todo = (f"beat the leader of {GYMS[k - 1]['name']}" if path == "warrior"
                else f"talk to the {JOBS[path].capitalize()}")
        strings[f"ladder_closed_{key}_{k}"] = (
            f"{speaker}: You can't come in here yet! {now} Head back to {town} and {todo} there.")
        events[f"Ladder closed {key} {k}"] = ev(
            [f"translated_dialog ladder_closed_{key}_{k}", f"clear_variable {pick.split(':')[0]}"],
            [f"is variable_set {pick}"] + open_conds(path, k) + [finished(path, k).replace("is ", "not ", 1)],
        )


# A pupil's bet comes before the townsperson (the first, easy rung of that
# path's ladder). Very easy on purpose for now (Stephen, 2026-11-25).
#   seen: show a species from the Tuxepedia taller than bar_cm.
#   team: put forward a team monster whose stat reaches bar (bar not told).
#   race: the same rule as team, told as a race against the pupil's runner.
PUPILS = {
    "researcher": {"path": "scholar", "name": "Pim", "kind": "seen", "bar_cm": 10},
    "collector": {"path": "seeker", "name": "Tay", "kind": "team", "stat": "melee", "bar": 5},
    # A race: the pupil's runner and its speed (the bar) are not told.
    "breeder": {"path": "keeper", "name": "Lin", "kind": "race", "stat": "speed", "bar": 5,
                "runner": "Lapinou"},
}

# Town N = route N, gym N, its townspeople and their pupils. Town 1's game
# variables have no suffix (old saves); town N's carry "_tN" (town_suffix).
# Satisfying any one path of town N sets ladder_stage:N+1, which opens town
# N+1.
# Menus (Stephen, 2026-11-25): main menu > Map > route 1, town 1, route 2,
# town 2...; a route lists its environments, a town its temples (the gym is
# the warrior's). ladder_at says which menu is open: hub (main), map,
# ladder_route_N, ladder_town_N, ladder_gym_N.
TOWNS = [
    {"name": "Willowby", "researcher": RESEARCHER, "collector": COLLECTOR, "breeder": BREEDER,
     "pupils": PUPILS},
    {
        "name": "Saltmere",
        "researcher": {"seen": (8, 8), "rewards": ["kits_10", "gift_pipis", "tm_frostbite"]},
        "collector": {"species": (4, 4), "rewards": ["tip_gym_2", "tip_route_2", "tm_frostbite"]},
        "breeder": {
            "monster": "dandicub", "name": "Daisy", "start": 5, "goal": (6, 8),
            "keep_rewards": ["kits_10", "tip_gym_2", "tm_frostbite"],
            "give_rewards": ["gift_eskipup", "kits_20", "gift_pipis"],
        },
        # Bars a little higher than town 1's; a level-5 team still passes
        # easily (level-5 starters: melee 47-96, speed 73-120; starters are
        # 60-80 cm tall).
        "pupils": {
            "researcher": {"path": "scholar", "name": "Wen", "kind": "seen", "bar_cm": 50},
            "collector": {"path": "seeker", "name": "Oda", "kind": "team", "stat": "melee", "bar": 10},
            "breeder": {"path": "keeper", "name": "Ruth", "kind": "race", "stat": "speed", "bar": 10,
                        "runner": "Pairagrin"},
        },
    },
    # Towns 3-6. Every pupil's bar is passable by a lone level-5 starter
    # (measured 2026-11-25 over 300 spawns each: melee 43-96, speed 65-122,
    # weight 18.0-26.4 kg; Tuxepedia heights agnite 80, squink 70, budaye 80
    # cm), so the bars stay below melee 43, speed 65 and 70 cm.
    {
        "name": "Stonebridge",
        "researcher": {"seen": (10, 40), "rewards": ["kits_10", "gift_eskipup", "tm_frostbite"]},
        "collector": {"species": (5, 5), "rewards": ["tip_gym_3", "tip_route_3", "tm_frostbite"]},
        "breeder": {
            "monster": "cardiling", "name": "Robin", "start": 6, "goal": (7, 9),
            "keep_rewards": ["kits_10", "tip_gym_3", "tm_frostbite"],
            "give_rewards": ["gift_pipis", "kits_20", "gift_eskipup"],
        },
        "pupils": {
            "researcher": {"path": "scholar", "name": "Ivo", "kind": "seen", "bar_cm": 55},
            "collector": {"path": "seeker", "name": "Kit", "kind": "team", "stat": "melee", "bar": 15},
            "breeder": {"path": "keeper", "name": "Mo", "kind": "race", "stat": "speed", "bar": 20,
                        "runner": "Foxfire"},
        },
    },
    {
        "name": "Emberfall",
        "researcher": {"seen": (12, 120), "rewards": ["kits_10", "gift_pipis", "tm_frostbite"]},
        "collector": {"species": (6, 6), "rewards": ["tip_gym_4", "tip_route_4", "tm_frostbite"]},
        "breeder": {
            "monster": "pickoon", "name": "Bandit", "start": 7, "goal": (8, 10),
            "keep_rewards": ["kits_10", "tip_gym_4", "tm_frostbite"],
            "give_rewards": ["gift_eskipup", "kits_20", "gift_pipis"],
        },
        "pupils": {
            "researcher": {"path": "scholar", "name": "Nell", "kind": "seen", "bar_cm": 60},
            "collector": {"path": "seeker", "name": "Ash", "kind": "team", "stat": "melee", "bar": 20},
            "breeder": {"path": "keeper", "name": "Pia", "kind": "race", "stat": "speed", "bar": 30,
                        "runner": "Pickoon"},
        },
    },
    {
        "name": "Irongate",
        "researcher": {"seen": (14, 250), "rewards": ["kits_10", "gift_eskipup", "tm_frostbite"]},
        "collector": {"species": (6, 6), "rewards": ["tip_gym_5", "tip_route_5", "tm_frostbite"]},
        "breeder": {
            "monster": "medipup", "name": "Patch", "start": 8, "goal": (9, 11),
            "keep_rewards": ["kits_10", "tip_gym_5", "tm_frostbite"],
            "give_rewards": ["gift_pipis", "kits_20", "gift_eskipup"],
        },
        "pupils": {
            "researcher": {"path": "scholar", "name": "Quin", "kind": "seen", "bar_cm": 65},
            "collector": {"path": "seeker", "name": "Rue", "kind": "team", "stat": "melee", "bar": 30},
            "breeder": {"path": "keeper", "name": "Sol", "kind": "race", "stat": "speed", "bar": 40,
                        "runner": "Botbot"},
        },
    },
    # The summit: each path's final tier. Satisfying one is that path's ending.
    {
        "name": "Highcrest",
        "researcher": {"seen": (16, 393), "rewards": ["kits_20", "gift_pipis", "tm_frostbite"]},
        # species caught (Tuxepedia), not a team
        "collector": {"caught": (10, 200), "rewards": ["tip_gym_6", "tip_route_6", "tm_frostbite"]},
        # show a team with evolved monsters: (stages, how many)
        "breeder": {"evolved": (("stage1:stage2", 1), ("stage2", 6)),
                    "rewards": ["kits_20", "tip_gym_6", "tm_frostbite"]},
        "pupils": {
            "researcher": {"path": "scholar", "name": "Tam", "kind": "seen", "bar_cm": 68},
            "collector": {"path": "seeker", "name": "Uma", "kind": "team", "stat": "melee", "bar": 40},
            "breeder": {"path": "keeper", "name": "Vic", "kind": "race", "stat": "speed", "bar": 55,
                        "runner": "Flummby"},
        },
    },
]
# The last town's paths end the game, each with its own message.
ENDINGS = {
    "warrior": "You have reached the summit of the warrior's path! No trainer is left who can stand "
               "against you. The title of Champion is yours.",
    "scholar": "You have reached the summit of the scholar's path! Your Tuxepedia is the finest there "
               "is, and every scholar now asks you first. The title of Loremaster is yours.",
    "seeker": "You have reached the summit of the seeker's path! There is no trail you have not "
              "walked and no hollow you have not searched. The title of Trailblazer is yours.",
    "keeper": "You have reached the summit of the keeper's path! Your monsters have grown under your "
              "care into their finest forms. The title of Guardian is yours.",
}


def town_suffix(n):
    """'' for town 1, '_t2' for town 2: appended to the town's variable names."""
    return "" if n == 1 else f"_t{n}"


# Variables that hold an answer between a choice closing and its handler
# running; menus wait while any is set. One per reward menu, so equal reward
# keys in different menus never fire each other's handlers.
PENDING = ["ladder_reward_researcher", "ladder_reward_collector",
           "ladder_reward_breeder_keep", "ladder_reward_breeder_give", "ladder_breeder_ans",
           "ladder_reward_rival", "ladder_settings_ans", "ladder_bet_pending"]
# Each later town has its own copy of the first five (its people's answers);
# a town whose breeder only asks to see a team has a plain reward menu.
PENDING += [v + town_suffix(n) for n in range(2, len(TOWNS) + 1) for v in PENDING[:5]]
PENDING += ["ladder_reward_breeder" + town_suffix(n) for n, t in enumerate(TOWNS, 1) if "evolved" in t["breeder"]]

# The rival (switchable: town menu > Test settings, game variable rule_rival
# on/off). After the FIRST townsperson or gym of a town is satisfied, the
# rival challenges the player in that person's path (tuxemon/combat/rival.py);
# in the last town, after every path satisfied.
RIVAL = {
    "sprite": "ceo",
    "default": "on",
    "win_rewards": ["kits_20", "gift_eskipup", "tm_frostbite"],
    # Rex's bets, one row per town, very easy on purpose (Stephen,
    # 2026-11-25): the monster he shows off and its size. tall: you show a
    # taller species from your Tuxepedia; heavy: you put forward a team
    # monster at least as heavy. (The keeper's bet draws a stat on the day
    # against a level-1 monster, rival.SHOW_LEVEL; the warrior's is a battle.)
    "bets": [
        {"tall": ("chickadee", 5), "heavy": ("hatchling", 0.5)},
        {"tall": ("cardiling", 20), "heavy": ("cardiling", 1)},
        # towns 3-6: the species' own Tuxepedia height and weight, below a lone
        # level-5 starter's (70 cm, 18 kg)
        {"tall": ("foxfire", 41), "heavy": ("botbot", 4)},
        {"tall": ("noctula", 50), "heavy": ("poinchin", 6)},
        {"tall": ("rockitten", 55), "heavy": ("pickoon", 8)},
        {"tall": ("lapinou", 60), "heavy": ("tourbidi", 14)},
    ],
}

NPC_POS = "5,3"

# Autosave: every town, route, gym and contest menu saves to the autosave
# slot as it opens. Menus open only when nothing is half done (no pick, busy,
# pending answer or rival contest due), so a save never catches a half-run
# event; in effect the game saves before and after every encounter and
# contest.

# Every action list that may complete a path sets this flag in the SAME list
# as it frees the menus. The engine checks every event's conditions before
# running any actions, so a separate "unlock" event and a menu could both
# start in one frame; menus wait while the flag is set, and resolver events
# (unlock or not) clear it.
CHECK = "set_variable ladder_check_unlock:yes"
ROOT = Path("mods/tuxemon")
PO = ROOT / "l18n/en_US/LC_MESSAGES/base.po"
BEGIN, END = "# --- ladder campaign (generated by scripts/ladder/gen.py) ---", "# --- end ladder campaign ---"


def trainer_slug(g, t):
    return f"ladder_g{g}_t{t}"


def ev(actions, conditions):
    return {"actions": actions, "conditions": conditions, "type": "event"}


_NAMES = {}


def monster_name(slug):
    """The monster's English name: the msgstr of base.po's msgid `slug`, read outside the generated block."""
    if not _NAMES:
        po = PO.read_text()
        if BEGIN in po:
            po = po.split(BEGIN, 1)[0] + po.split(END, 1)[1]
        _NAMES.update(re.findall(r'^msgid "([^"]+)"\nmsgstr "([^"]+)"$', po, re.M))
    if slug not in _NAMES:
        raise SystemExit(f"no English name for monster {slug!r} in base.po")
    return _NAMES[slug]


def longest(words):
    return max(len(w) for w in words)


def var_bounds():
    """The longest value each ${{var:...}} placeholder in a text can take, as text of that many characters.

    Monster names: the longest species name, or 15 (the game's nickname limit,
    PLAYER_NAME_LIMIT). Numbers and sizes: 9 characters ('1000.0 lb'). Stat names:
    8. Rank titles: the longest title of PATHS. The rival switch: 'off'.
    """
    monster_name("hatchling")  # fills _NAMES
    species = [_NAMES[f.stem] for f in (ROOT / "db/monster").glob("*.yaml") if f.stem in _NAMES]
    name, value = max(15, longest(species)), 9
    out = {k: "x" * name for k in ("ladder_bet_name", "ladder_contest_your_monster", "ladder_contest_rival_monster")}
    out.update({k: "x" * value for k in ("ladder_bet_value", "ladder_contest_you", "ladder_contest_rival")})
    out["ladder_contest_stat_name"] = "x" * 8
    out["rule_rival"] = "off"
    for p, titles in PATHS.items():
        out[f"ladder_rank_{p}_title"] = "x" * longest(titles)
        out[f"ladder_rank_show_{p}"] = "x" * max(longest(titles), len("no rank yet"))
    return out


def substitute(text, bounds=None):
    """`text` with every ${{var:key}} replaced by its longest value; an unknown placeholder is an error."""
    bounds = bounds or var_bounds()

    def one(m):
        if m.group(1) not in bounds:
            raise SystemExit(f"placeholder with no length bound: {m.group(0)} (add it to var_bounds)")
        return bounds[m.group(1)]

    left = re.sub(r"\$\{\{var:([^}]+)\}\}", one, text)
    if "${{" in left:
        raise SystemExit(f"placeholder that is not ${{{{var:...}}}}: {text!r}")
    return left


def pages_of(text, bounds=None):
    """Split `text` into pages that fit: at the author's PAGE_BREAKs, then at sentence ends, then at clauses.

    Sentences (and, for one too long, clauses) are packed greedily into a page
    while it still fits. Never cuts a word; stops if one clause cannot fit.
    """
    bounds = bounds or var_bounds()
    out = []
    for chunk in text.split(PAGE_BREAK):
        if fits(chunk, bounds):
            out.append(chunk)
            continue
        units = []
        for sentence in re.split(r"(?<=[.!?])\s+(?=[^.\s])", chunk):
            if fits(sentence, bounds):
                units.append(sentence)
            else:
                units += re.split(r"(?<=[;,:])\s+", sentence)
        page = ""
        for u in units:
            if not fits(u, bounds):
                raise SystemExit(f"one clause does not fit a dialog page ({COLS}x{ROWS}): {u!r}")
            if page and not fits(f"{page} {u}", bounds):
                out.append(page)
                page = u
            else:
                page = f"{page} {u}".strip()
        out.append(page)
    return out


def paginate(events, strings):
    """Split every dialog text that is over the budget into pages, one translated_dialog each.

    The first page keeps the text's key; page n gets key + '_pn'. Every
    `translated_dialog key` action becomes one per page. Returns {key: pages}
    for the keys that were split.
    """
    bounds = var_bounds()
    split = {}
    for e in events.values():
        for a in e["actions"]:
            if a.startswith("translated_dialog "):
                key = a.split(" ", 1)[1]
                pages = pages_of(strings[key], bounds)
                if len(pages) > 1:
                    split[key] = pages
    for key, pages in split.items():
        strings[key] = pages[0]
        for n, page in enumerate(pages[1:], 2):
            assert f"{key}_p{n}" not in strings, key
            strings[f"{key}_p{n}"] = page
    for e in events.values():
        acts = []
        for a in e["actions"]:
            acts.append(a)
            if a.startswith("translated_dialog "):
                key = a.split(" ", 1)[1]
                acts += [f"translated_dialog {key}_p{n}" for n in range(2, len(split.get(key, ())) + 1)]
        e["actions"] = acts
    return split


def names(team):
    """'Lambert, Fruitera and Chloragon'."""
    n = [monster_name(m) for m, _ in team]
    return n[0] if len(n) == 1 else ", ".join(n[:-1]) + " and " + n[-1]


def weak_to(element):
    """Elements that hit `element` for double damage."""
    out = []
    for f in sorted((ROOT / "db/element").glob("*.yaml")):
        d = yaml.safe_load(f.read_text())
        if any(t["against"] == element and t["multiplier"] > 1 for t in d["types"]):
            out.append(d["slug"])
    return out


def choice(options, var, back=None, must=False, title=None):
    """Actions for a choice list whose answer lands in `var`.

    back: the key of a marked last row. Back and Cancel choose it (the list
    closes without an answer, and default_variable then sets the answer to
    the row), so the row's label names where Back leads. must: Back does
    nothing. Neither: Back closes the list and the event asks again.
    title: a string key shown as a header on the list (not a row).
    """
    rows = list(options) + ([back] if back else [])
    actions = [f"translated_dialog_choice {':'.join(rows)},{var}" + (f",{title}" if title else "") + (",must" if must else "")]
    return actions + ([f"default_variable {var}:{back}"] if back else [])


def reward_menu(events, strings, who, keys, then, later=False):
    """A choice of rewards; picking one runs its actions, then `then`.

    A reward list must be answered: Back and Cancel do nothing (Stephen,
    2026-11-25). later=True would add the marked last row "Decide later
    [Back]" (the person asks again next visit); no list uses it now.
    """
    pick_var = "ladder_reward_" + who.replace(" ", "_")
    assert pick_var in PENDING, pick_var
    for key in keys:
        label, actions = REWARDS[key]
        strings[f"ladder_reward_{key}"] = label
        if not any(a.startswith("translated_dialog") for a in actions):
            strings[f"ladder_got_{key}"] = f"You received {label[0].lower() + label[1:]}."
            actions = actions + [f"translated_dialog ladder_got_{key}"]
        events[f"Ladder {who} reward {key}"] = ev(
            actions + then + [f"clear_variable {pick_var}"],
            [f"is variable_set {pick_var}:ladder_reward_{key}"],
        )
    if later:
        strings["ladder_reward_later"] = "Decide later [Back]"
        events[f"Ladder {who} reward later"] = ev(
            [f"clear_variable {pick_var}"],
            [f"is variable_set {pick_var}:ladder_reward_later"],
        )
    return choice(["ladder_reward_" + k for k in keys], pick_var,
                  back="ladder_reward_later" if later else None, must=not later)


def people_events(events, strings, pick, busy, idle, unlock_sources, tn=1):
    """Researcher, collector and breeder of town tn (and their pupils)."""
    town, s, T = TOWNS[tn - 1], town_suffix(tn), "" if tn == 1 else f" T{tn}"
    g1 = GYMS[tn - 1]
    leader_team = g1["trainers"][-1][2]
    strings[f"ladder_tip_gym_{tn}"] = (
        f"{g1['trainers'][-1][1]} uses {names(leader_team)}, level {leader_team[0][1]}. "
        f"{GYM_TYPES[tn - 1].capitalize()} monsters are weak against "
        f"{', '.join(weak_to(GYM_TYPES[tn - 1]))}."
    )
    weak = set(weak_to(GYM_TYPES[tn - 1]))
    # one lead line, then one page per area; an area whose list is too long keeps its first few
    pages = [f"{GYM_TYPES[tn - 1].capitalize()} monsters fear these on {ROUTES[tn - 1]['name'].split(':')[0]}."]
    for area in ROUTES[tn - 1]["areas"]:
        hits = []
        for m in area["monsters"]:
            d = yaml.safe_load((ROOT / f"db/monster/{m}.yaml").read_text())
            if weak.intersection(d["types"]) and len(hits) < 3:  # a few per area is tip enough
                hits.append(monster_name(m))
        for keep in range(len(hits), 0, -1):
            page = f"{area['key'].capitalize()}: {', '.join(hits[:keep])}" + ("." if keep == len(hits) else " and others.")
            if fits(page):
                break
        if hits:
            pages.append(page)
    strings[f"ladder_tip_route_{tn}"] = PAGE_BREAK.join(pages)
    strings["ladder_got_eskipup"] = "Eskipup joins your team."
    strings["ladder_got_pipis"] = "Pipis joins your team."
    for job in ("researcher", "collector", "breeder"):
        strings[f"ladder_{job}{s}"] = f"{town['pupils'][job]['path'].capitalize()} temple"
    strings["ladder_thanks"] = "Thank you again! Come back any time."
    strings["ladder_pick_reward"] = "Please choose a reward."

    def visit(who, conds, actions):
        events[f"Ladder{T} {who}"] = ev(
            [f"clear_variable {pick}", f"set_variable {busy}:yes"] + actions, conds
        )

    def pupil(who):
        """The pupil's bet: asked every visit until won. Returns the gate."""
        p = town["pupils"][who]
        job, who = who, who + s  # who: this town's copy of the variables and text
        title = f"{PATHS[p['path']][tn - 1]} {p['name']}"  # town N's pupils carry title N
        won, pend, b = f"ladder_pupil_{who}:done", "ladder_bet_pending", "ladder_bet_"
        var = lambda k: "${{var:" + b + k + "}}"  # noqa: E731
        if p["kind"] == "seen":
            show = [f"choice_seen_monster {b}pick", f"pupil_bet seen,{b}pick,{p['bar_cm']}"]
            strings.update({
                f"ladder_{who}_bet_ask": f"{title}: You want the {job.capitalize()}? First, a bet! I bet you "
                                         f"have never seen a monster taller than {p['bar_cm']} cm. "
                                         f"Show me one from your Tuxepedia!",
                f"ladder_{who}_bet_win": f"{title}: Wow, {var('name')}! You have really seen one? And it was "
                                         f"{var('value')} tall! Whoa, I'm so jealous. "
                                         f"You must have explored a lot!",
                f"ladder_{who}_bet_lose": f"{title}: {var('name')}? That is only {var('value')} tall. "
                                          f"I knew it! Come back when you have seen a taller one.",
            })
        elif p["kind"] == "race":
            show = [f"get_player_monster {b}mon", f"pupil_bet team,{b}mon,{p['stat']},{p['bar']}"]
            stat, runner = p["stat"].capitalize(), monster_name(p["runner"].lower())
            strings.update({
                f"ladder_{who}_bet_ask": f"{title}: You want the {job.capitalize()}? First, a race! My {runner} "
                                         f"against one of yours, once round the yard. I bet mine is faster. "
                                         f"Pick your runner!",
                f"ladder_{who}_bet_win": f"They're off! ... Your {var('name')} shoots past {runner} on the last "
                                         f"bend! {title}: Whoa, {stat} {var('value')}! You have raised that "
                                         f"one well. I'm so jealous!",
                f"ladder_{who}_bet_lose": f"They're off! ... {runner} crosses the line first, your "
                                          f"{var('name')} well behind. {title}: Ha! Come back with a faster one.",
            })
        else:
            show = [f"get_player_monster {b}mon", f"pupil_bet team,{b}mon,{p['stat']},{p['bar']}"]
            strings.update({
                f"ladder_{who}_bet_ask": f"{title}: You want the {job.capitalize()}? First, a bet! See this "
                                         f"rock? I bet none of your monsters can lift it. "
                                         f"Put one forward and let it try!",
                f"ladder_{who}_bet_win": f"{title}: Whoa! Your {var('name')} lifted it clean off the ground! "
                                         f"Where did you find one that strong? I'm so jealous!",
                f"ladder_{who}_bet_lose": f"Your {var('name')} strains and strains... the rock does not move. "
                                          f"{title}: Ha! Come back with a stronger one.",
            })
        strings[f"ladder_{who}_bet_none"] = f"{title}: Nothing to show me? Come back when you are ready."
        strings[f"ladder_{who}_bet_pass"] = f"{title}: Go on in, the {job.capitalize()} will see you now."
        door = open_conds(p["path"], tn)  # earlier temples of this path finished
        closed_door(events, strings, who, f"{pick}:ladder_{who}", title, p["path"], tn)
        visit(f"{who} pupil", [f"is variable_set {pick}:ladder_{who}", f"not variable_set {won}"] + door,
              [f"translated_dialog ladder_{who}_bet_ask"] + show
              + [f"set_variable {pend}:{who}", f"clear_variable {busy}"])
        for result, after in (("win", [f"set_variable {won}", f"translated_dialog ladder_{who}_bet_pass"]),
                              ("lose", []), ("none", [])):
            events[f"Ladder {who} pupil {result}"] = ev(
                [f"translated_dialog ladder_{who}_bet_{result}"] + after + [f"clear_variable {pend}"],
                [f"is variable_set {pend}:{who}", f"is variable_set {b}result:{result}"],
            )
        return [f"is variable_set {won}"]

    def simple(who, met, request, glad, rewards):
        gate = pupil(who) if who in town["pupils"] else []
        path = town["pupils"][who]["path"]
        who += s  # this town's copy of the variables, text and events
        done = f"ladder_{who}:done"
        here = [f"is variable_set {pick}:ladder_{who}"] + open_conds(path, tn) + gate
        strings[f"ladder_{who}_request"] = request
        strings[f"ladder_{who}_glad"] = glad
        visit(f"{who} done", here + [f"is variable_set {done}"],
              ["translated_dialog ladder_thanks", f"clear_variable {busy}"])
        visit(f"{who} not yet", here + [f"not variable_set {done}", f"not {met}"],
              [f"translated_dialog ladder_{who}_request", f"clear_variable {busy}"])
        rewards_choice = reward_menu(events, strings, who, rewards,
                             [f"set_variable {done}"] + rank_up(path, tn) + [CHECK, f"clear_variable {busy}"])
        visit(f"{who} ready", here + [f"not variable_set {done}", f"is {met}"],
              [f"translated_dialog ladder_{who}_glad", "translated_dialog ladder_pick_reward"] + rewards_choice
              + [f"clear_variable {busy}"])
        unlock_sources.append((who, f"is variable_set {done}"))

    n = req(town["researcher"]["seen"])
    simple("researcher", f"tuxepedia greater_or_equal,1.0,{n}",
           f"I study monsters. Come back when your Tuxepedia lists {n} species.",
           f"{n} species already! That helps my research a lot.",
           town["researcher"]["rewards"])
    c = town["collector"]
    if "caught" in c:  # the summit: species caught, counted in the Tuxepedia
        n = req(c["caught"])
        simple("collector", f"tuxepedia_caught greater_or_equal,{n}",
               f"A true seeker catches everything. Come back when you have caught {n} different species!",
               f"{n} species caught! There is hardly a hollow you have not searched.",
               c["rewards"])
    else:
        n = req(c["species"])
        simple("collector", f"party_species greater_or_equal,{n}",
               f"I love seeing monsters. Show me a team with {n} different species!",
               f"{n} different species in one team, how lovely! Thank you for showing me.",
               c["rewards"])

    b = town["breeder"]
    if "evolved" in b:  # the summit: show a team of evolved monsters
        stages, n = req(b["evolved"])
        what = "fully evolved (stage 2)" if stages == "stage2" else "evolved"
        many = f"{n} {what} monsters" if n > 1 else f"a {what} monster"
        simple("breeder", f"party_stage {stages},greater_or_equal,{n}",
               f"A keeper's work shows in the monsters raised. Show me a team with {many}!",
               f"Look at them! You have raised {many}. A keeper could ask no more.",
               b["rewards"])
        return

    # Breeder: lends Billy, asks to see him at the goal level, then the player
    # keeps Billy (smaller reward) or gives Billy back (bigger reward).
    name, mon = b["name"], monster_name(b["monster"])
    state, ans, billy = f"ladder_breeder{s}", f"ladder_breeder_ans{s}", f"ladder_billy{s}"
    here = [f"is variable_set {pick}:{state}"] + open_conds("keeper", tn) + pupil("breeder")
    # text keys ladder_breeder_offer etc. (town 1), ladder_breeder_t2_offer (town 2)
    strings.update({f"{state}_{k}": v for k, v in {
        "offer": f"This is {name}, my {mon}. Would you raise {name} until level {req(b['goal'])}?",
        "yes": f"Raise {name}",
        "no": "Not now [Back]",
        "joined": f"{name} joins your team. Take good care of {name}!",
        "waiting": f"How is {name}? Show me {name} in your team at level {req(b['goal'])}.",
        "ready": f"{name} has grown so much! Will {name} stay with you, or come home with me?",
        "later": "Decide later [Back]",
        "keep": f"{name} stays with me (small reward)",
        "give": f"{name} goes home (big reward)",
        "kept": f"{name} is happy with you. Here is something for your trouble.",
        "given": f"Welcome home, {name}! Thank you so much. Choose anything you like.",
    }.items()})
    visit("breeder done", here + [f"is variable_set {state}:done"],
          ["translated_dialog ladder_thanks", f"clear_variable {busy}"])
    visit("breeder offer", here + [f"not variable_set {state}"],
          [f"translated_dialog {state}_offer",
           *choice([f"{state}_yes"], ans, back=f"{state}_no"),
           f"clear_variable {busy}"])
    events[f"Ladder{T} breeder accept"] = ev(
        [f"add_monster {b['monster']},{b['start']}",
         f"copy_variable {billy},add_monster", f"set_monster_attribute {billy},name,{name}",
         f"set_variable {state}:raising", f"translated_dialog {state}_joined",
         f"clear_variable {ans}"],
        [f"is variable_set {ans}:{state}_yes"],
    )
    events[f"Ladder{T} breeder decline"] = ev(
        [f"clear_variable {ans}"],
        [f"is variable_set {ans}:{state}_no"],
    )
    goal = req(b["goal"])
    level = f"monster_level {billy},greater_or_equal,{goal}"
    visit("breeder waiting", here + [f"is variable_set {state}:raising", f"not {level}"],
          [f"translated_dialog {state}_waiting", f"clear_variable {busy}"])
    visit("breeder ready", here + [f"is variable_set {state}:raising", f"is {level}"],
          [f"translated_dialog {state}_ready",
           *choice([f"{state}_keep", f"{state}_give"], ans, back=f"{state}_later"),
           f"clear_variable {busy}"])
    events[f"Ladder{T} breeder later"] = ev(
        [f"clear_variable {ans}"],
        [f"is variable_set {ans}:{state}_later"],
    )
    finish = [f"set_variable {state}:done"] + rank_up("keeper", tn) + [CHECK, f"clear_variable {busy}"]
    keep = reward_menu(events, strings, "breeder keep" + s, b["keep_rewards"], finish)
    events[f"Ladder{T} breeder keep"] = ev(
        [f"translated_dialog {state}_kept"] + keep + [f"clear_variable {ans}"],
        [f"is variable_set {ans}:{state}_keep"],
    )
    give = reward_menu(events, strings, "breeder give" + s, b["give_rewards"],
                       [f"remove_monster {billy}"] + finish)
    events[f"Ladder{T} breeder give"] = ev(
        [f"translated_dialog {state}_given"] + give + [f"clear_variable {ans}"],
        [f"is variable_set {ans}:{state}_give"],
    )
    unlock_sources.append(("breeder" + s, f"is variable_set {state}:done"))


def rival_events(events, strings, pick, busy, idle, tn=1):
    """The rival's contest in town tn and the on/off switch. Returns the NPC.

    Called once per town; the switch, the shared text and the reward menu come
    out the same every time. Town tn's contest states carry its suffix.
    """
    s, T = town_suffix(tn), "" if tn == 1 else f" T{tn}"
    rs = f"ladder_rival_t{tn}"
    pend = "ladder_rival_pending"
    on = ["is variable_set rule_rival:on"]
    c = "ladder_contest_"
    v = lambda k: "${{var:" + c + k + "}}"  # noqa: E731
    bet = lambda k: "${{var:ladder_bet_" + k + "}}"  # noqa: E731
    row = RIVAL["bets"][tn - 1]
    (tall, tall_cm), (heavy, heavy_kg) = [(monster_name(m), n) for m, n in (row["tall"], row["heavy"])]
    strings.update({
        "ladder_settings": "Test settings",
        "ladder_settings_now": "Rival contests are ${{var:rule_rival}}.",
        "ladder_rival_on": "Rival: on",
        "ladder_rival_off": "Rival: off",
        "ladder_settings_none": "No change [Back]",
        rs: "Rival Rex",
        f"ladder_rival_intro{s}": (
            "Rex: Hey, freebie collector! My team came from the Monster Mall, "
            "top of the range. Think you can beat money? Let's settle it right here!" if tn == 1 else
            f"Rex: You again? I bought a whole new team for {TOWNS[tn - 1]['name']}, "
            "the newest models. Let's settle it right here!"),
        "ladder_contest_breeder_ask": f"Rex: I bought this one this morning, pure pedigree. I bet it has "
                                      f"better {v('stat_name')} than anything you have raised. "
                                      f"Put one forward!",
        "ladder_contest_stat_result": f"Your {v('your_monster')}: {v('stat_name')} {v('you')}. "
                                      f"Rex's {v('rival_monster')}: {v('rival')}.",
        f"ladder_contest_researcher_ask{s}": f"Rex: Behold my {tall}: {tall_cm} cm of pure pedigree, the tallest "
                                             f"money can buy! I bet you have never even seen a taller monster. "
                                             f"Show me one from your Tuxepedia, if you can!",
        f"ladder_contest_tall_result{s}": f"Your {bet('name')}: {bet('value')} tall. Rex's {tall}: {tall_cm} cm.",
        f"ladder_contest_collector_ask{s}": f"Rex: Feel the weight of my {heavy}: {heavy_kg} kg, the heaviest "
                                            f"money can buy! I bet nothing on your team weighs as much. "
                                            f"Put one forward!",
        f"ladder_contest_heavy_result{s}": f"Your {bet('name')}: {bet('value')}. Rex's {heavy}: {heavy_kg} kg.",
        "ladder_contest_gym_ask": "Rex: I bet you can't beat my newest purchase. Battle me!",
        "ladder_rival_win": "Rex: What?! They sold me these as the best out there! I'll just have to pay more. "
                            "...Fine, take this, I can buy another.",
        "ladder_rival_lose": "Rex: Ha! Your free monsters still can't compete with my expensive team!",
        "ladder_rival_draw": "Rex: A draw?! I want a refund.",
        "ladder_rival_none": "Rex: Nothing to show? Ha! I knew it.",
    })
    # switch
    events["Ladder Open settings"] = ev(
        ["translated_dialog ladder_settings_now",
         *choice(["ladder_rival_on", "ladder_rival_off"], "ladder_settings_ans", back="ladder_settings_none"),
         f"clear_variable {pick}"],
        [f"is variable_set {pick}:ladder_settings"],
    )
    for val in ("on", "off"):
        events[f"Ladder rival {val}"] = ev(
            [f"set_variable rule_rival:{val}", "clear_variable ladder_settings_ans"],
            [f"is variable_set ladder_settings_ans:ladder_rival_{val}"],
        )
    events["Ladder settings none"] = ev(
        ["clear_variable ladder_settings_ans"],
        ["is variable_set ladder_settings_ans:ladder_settings_none"],
    )
    events["Ladder rival skipped"] = ev(
        [f"clear_variable {pend}"],
        [f"is variable_set {pend}", "not variable_set rule_rival:on"],
    )
    start = lambda kind: idle + on + [  # noqa: E731
        f"is variable_set {pend}:{kind}{s}"]
    head = [f"set_variable {busy}:yes", f"translated_dialog ladder_rival_intro{s}"]
    tail = [f"set_variable {pend}:result{s}", f"clear_variable {busy}"]
    events[f"Ladder{T} rival breeder"] = ev(
        head + ["rival_contest pick_stat", "translated_dialog ladder_contest_breeder_ask",
                f"get_player_monster {c}mon", f"rival_contest stat,{c}mon",
                "translated_dialog ladder_contest_stat_result"] + tail,
        start("breeder"),
    )
    # scholar and seeker: the pupils' rules (pupil_bet) against Rex's monster;
    # the player must show something, so there is always a result.
    events[f"Ladder{T} rival researcher"] = ev(
        head + [f"translated_dialog ladder_contest_researcher_ask{s}",
                "choice_seen_monster ladder_bet_pick,must", f"pupil_bet seen,ladder_bet_pick,{tall_cm}",
                f"copy_variable {c}result,ladder_bet_result",
                f"translated_dialog ladder_contest_tall_result{s}"] + tail,
        start("researcher"),
    )
    events[f"Ladder{T} rival collector"] = ev(
        head + [f"translated_dialog ladder_contest_collector_ask{s}",
                "get_player_monster ladder_bet_mon", f"pupil_bet team,ladder_bet_mon,weight,{heavy_kg}",
                f"copy_variable {c}result,ladder_bet_result",
                f"translated_dialog ladder_contest_heavy_result{s}"] + tail,
        start("collector"),
    )
    # gym: a battle against one monster that counters the player's lead, at
    # level = the town's number (1, 2, 3...), so the player always wins for
    # now (Stephen, 2026-11-25: difficulty is not being tuned yet)
    events[f"Ladder{T} rival gym"] = ev(
        head + ["translated_dialog ladder_contest_gym_ask", "set_environment interior",
                f"create_npc {rs},{NPC_POS}", f"rival_contest team,{rs},{tn}",
                f"start_battle player,{rs}", f"remove_npc {rs}",
                f"set_variable {pend}:battled{s}", f"clear_variable {busy}"],
        start("gym"),
    )
    events[f"Ladder{T} rival gym won"] = ev(
        [f"set_variable {c}result:win", f"set_variable {pend}:result{s}"],
        [f"is variable_set {pend}:battled{s}", f"is battle_outcome player,won,{rs}"],
    )
    events[f"Ladder{T} rival gym lost"] = ev(
        [f"set_variable {c}result:lose", f"set_variable {pend}:result{s}"],
        [f"is variable_set {pend}:battled{s}", f"not battle_outcome player,won,{rs}"],
    )
    # outcome, shared by every contest
    res = lambda r: idle + [f"is variable_set {pend}:result{s}", f"is variable_set {c}result:{r}"]  # noqa: E731
    done = [f"clear_variable {pend}", f"set_variable {rs}:done"]
    rewards_choice = reward_menu(events, strings, "rival", RIVAL["win_rewards"], [], later=False)
    events[f"Ladder{T} rival win"] = ev(
        [f"set_variable {busy}:yes", "translated_dialog ladder_rival_win",
         "translated_dialog ladder_pick_reward"] + rewards_choice + done + [f"clear_variable {busy}"],
        res("win"),
    )
    for r in ("lose", "draw", "none"):
        events[f"Ladder{T} rival {r}"] = ev(
            [f"translated_dialog ladder_rival_{r}"] + done, res(r),
        )
    return {
        "slug": rs,
        "speech": {"profile": {"default": {
            "pre_battle": None, "post_battle_win": None,
            "post_battle_lose": None, "post_battle_draw": None,
        }}},
        "combat": {},
        "audio": {},
        "template": {"sprite_name": RIVAL["sprite"], "combat_sheet": RIVAL["sprite"], "slug": RIVAL["sprite"]},
    }


def build():
    strings = {
        "ladder_campaign": "Tuxemon: The Four Paths",
        "ladder_welcome": "Welcome to the Ladder. Pick a partner to start with.",
        "ladder_team": "Team",
        "ladder_menu": "Menu (bag, save...)",
        "ladder_storage": "Storage",
        "ladder_fight": "Fight the next trainer",
        "ladder_leave": "Leave",
        "ladder_back": "Back",
        "ladder_back_main": "Main menu [Back]",
        "ladder_back_map": "Map [Back]",
        "ladder_title": "The Four Paths",
        "ladder_main": "What now?",
        "ladder_map": "Map",
        "ladder_map_where": "Where to?",
        "ladder_gym_done": "You have beaten every trainer here.",
        "ladder_all_done": "That's every gym there is for now. Well done!",
    }
    for p in PATHS:
        strings[f"ladder_rank_up_{p}"] = f"You now hold the rank of ${{{{var:ladder_rank_{p}_title}}}} on the {p}'s path!"
        strings[f"ladder_rank_line_{p}"] = f"{p.capitalize()}: ${{{{var:ladder_rank_show_{p}}}}}"
    strings["ladder_ranks"] = "Ranks"
    strings["ladder_rank_none"] = "no rank yet"
    events = {}
    pick = "ladder_pick"
    # A battle event clears the pick as its first action (so it cannot fire
    # twice: the battle record changes mid-battle, which would make the next
    # trainer's event true) and holds ladder_busy until the battle is over,
    # so no menu opens in between.
    busy = "ladder_busy"
    # Choices can be closed with Back/Escape, so no menu may hold `busy` across
    # a choice; instead the menus also wait while an answer is pending. A
    # handler clears its answer variable as its LAST action: a state pushed
    # by an action (a dialog) is not on top until the next frame, so clearing
    # first would let a menu open underneath it. (A running event is never
    # restarted, so this is safe.)
    idle = ["is current_state WorldState", f"not variable_set {pick}", f"not variable_set {busy}"]
    idle += [f"not variable_set {v}" for v in PENDING]
    # The town, route and gym menus also wait while a rival contest is due
    # or running, so the rival speaks as soon as the town goes quiet.
    menu_idle = idle + ["not variable_set ladder_rival_pending", "not variable_set ladder_unlock_msg",
                        "not variable_set ladder_check_unlock"]

    # Rules of this campaign that are not being tuned yet (Stephen,
    # 2026-11-25): every capture succeeds. Set here, not only at the start, so
    # saves made before the rule existed get it too.
    events["Ladder Rules"] = ev(["set_variable rule_sure_capture:true"], ["not variable_set rule_sure_capture"])
    events["Ladder Environment"] = ev(
        ["set_environment interior"], ["not environment_is interior"]
    )
    # The campaign menu leaves its gradient background (ImageState) on top of
    # the world; the other campaigns clear it with a bare change_bg. Without
    # this every "is current_state WorldState" event waits forever.
    events["Ladder Clear Background"] = ev(["change_bg"], ["is current_state ImageState"])
    events["Ladder Starter"] = ev(
        [
            "translated_dialog ladder_welcome",
            *choice(STARTERS, "ladder_starter", must=True),
        ],
        ["is current_state WorldState", "not variable_set ladder_starter"],
    )
    for s in STARTERS:
        events[f"Ladder Starter {s}"] = ev(
            [
                f"add_monster {s},{STARTER_LEVEL}",
                f"add_item tuxeball,{KITS}",
                "add_item nu_phone",
                "add_item app_tuxepedia",
                "add_item app_field_notes",
                "set_variable ladder_starter:done",
                f"set_variable rule_rival:{RIVAL['default']}",
            ],
            [f"is variable_set ladder_starter:{s}"],
        )

    # Main menu, the map (one per stage: stage k = towns 1..k unlocked, town k
    # opens when any path of town k-1 is satisfied) and a menu per town.
    n = len(TOWNS)
    assert len(ROUTES) == len(GYMS) == len(GYM_TYPES) == n
    opts = ["ladder_map", "ladder_ranks", "ladder_team", "ladder_storage", "ladder_menu", "ladder_settings"]
    events["Ladder Hub"] = ev(
        ["autosave", *choice(opts, pick, must=True, title="ladder_title")],
        menu_idle + ["is variable_set ladder_at:hub", "is variable_set ladder_starter:done"],
    )
    events["Ladder Open map"] = ev(
        ["set_variable ladder_at:map", f"clear_variable {pick}"],
        ["is variable_set ladder_at:hub", f"is variable_set {pick}:ladder_map"],
    )
    for stage in range(1, n + 2):
        opts = [f"ladder_{kind}_{t}" for t in range(1, min(stage, n) + 1) for kind in ("route", "town")]
        events[f"Ladder Map Stage {stage}"] = ev(
            ["autosave", *choice(opts, pick, back="ladder_back_main", title="ladder_map")],
            menu_idle + ["is variable_set ladder_at:map", f"is variable_set ladder_stage:{stage}"],
        )
    events["Ladder Map back"] = ev(
        ["set_variable ladder_at:hub", f"clear_variable {pick}"],
        ["is variable_set ladder_at:map", f"is variable_set {pick}:ladder_back_main"],
    )
    for t, town in enumerate(TOWNS, 1):
        s = town_suffix(t)
        slug = f"ladder_town_{t}"
        strings[slug] = town["name"]
        strings[f"{slug}_where"] = f"{town['name']}. Which temple?"
        strings[f"ladder_back_town_{t}"] = f"{town['name']} [Back]"
        events[f"Ladder Go Town {t}"] = ev(
            [f"set_variable ladder_at:{slug}", f"clear_variable {pick}"],
            ["is variable_set ladder_at:map", f"is variable_set {pick}:{slug}"],
        )
        opts = [f"ladder_gym_{t}", f"ladder_researcher{s}", f"ladder_collector{s}", f"ladder_breeder{s}"]
        events[f"Ladder Town {t} Menu"] = ev(
            ["autosave", *choice(opts, pick, back="ladder_back_map", title=slug)],
            menu_idle + [f"is variable_set ladder_at:{slug}"],
        )
        # Back goes up one level: a town and its route to the map, a gym to its town.
        for here, up, back in ((slug, "map", "ladder_back_map"), (f"ladder_route_{t}", "map", "ladder_back_map"),
                               (f"ladder_gym_{t}", slug, f"ladder_back_town_{t}")):
            events[f"Ladder Leave {here}"] = ev(
                [f"set_variable ladder_at:{up}", f"clear_variable {pick}"],
                [f"is variable_set ladder_at:{here}", f"is variable_set {pick}:{back}"],
            )
    events["Ladder Open ranks"] = ev(
        [f"rank_show {p},{strings['ladder_rank_none']}" for p in PATHS]
        + [f"translated_dialog ladder_rank_line_{p}" for p in PATHS]
        + [f"clear_variable {pick}"],
        [f"is variable_set {pick}:ladder_ranks"],
    )
    for which in ("team", "world"):
        key = "ladder_team" if which == "team" else "ladder_menu"
        events[f"Ladder Open {which}"] = ev(
            [f"open_menu {which}", f"clear_variable {pick}"],
            [f"is variable_set {pick}:{key}"],
        )
    events["Ladder Open storage"] = ev(
        ["access_pc player", f"clear_variable {pick}"],
        [f"is variable_set {pick}:ladder_storage"],
    )
    for i, route in enumerate(ROUTES, 1):
        slug = f"ladder_route_{i}"
        strings[slug] = route["name"]
        strings[f"{slug}_intro"] = route["intro"]
        strings[f"{slug}_where"] = "Where do you search?"
        # Arriving: describe each area once (the hints); the menu then lists
        # the areas by name only.
        events[f"Ladder Go Route {i}"] = ev(
            [f"set_variable {busy}:yes", f"set_variable ladder_at:{slug}", f"clear_variable {pick}",
             f"translated_dialog {slug}_intro"]
            + [f"translated_dialog {slug}_{a['key']}_hint" for a in route["areas"]]
            + [f"clear_variable {busy}"],
            ["is variable_set ladder_at:map", f"is variable_set {pick}:{slug}"],
        )
        area_keys = [f"{slug}_{a['key']}" for a in route["areas"]]
        events[f"Ladder Route {i} Menu"] = ev(
            ["autosave", *choice(area_keys, pick, back="ladder_back_map", title=slug)],
            menu_idle + [f"is variable_set ladder_at:{slug}"],
        )
        lo, hi = route["levels"]
        for area in route["areas"]:
            table_slug = f"{slug}_{area['key']}"
            strings[table_slug] = area["label"]
            strings[f"{table_slug}_hint"] = area["hint"]
            events[f"Ladder Route {i} {area['key']}"] = ev(
                [f"clear_variable {pick}", f"set_variable {busy}:yes",
                 f"set_environment {area['environment']}",
                 f"random_encounter {table_slug},100", f"clear_variable {busy}"],
                [f"is variable_set ladder_at:{slug}", f"is variable_set {pick}:{table_slug}"],
            )
            table = {
                "slug": table_slug,
                "monsters": [
                    {
                        "encounter_rate": weight,
                        "exp_req_mod": 1,
                        "held_items": [],
                        "level_range": [lo, hi],
                        "monster": m,
                        "variables": [],
                    }
                    for m, weight in area["monsters"].items()
                ],
            }
            (ROOT / f"db/encounter/{table_slug}.yaml").write_text(yaml.safe_dump(table, sort_keys=False))

    npcs = []
    unlock_sources = {t: [] for t in range(1, len(TOWNS) + 1)}  # town -> [(name, condition)]
    for g, gym in enumerate(GYMS, 1):
        slug = f"ladder_gym_{g}"
        strings[slug] = "Warrior temple"
        strings[f"{slug}_title"] = gym["name"]
        trainers = gym["trainers"]
        leader = trainer_slug(g, len(trainers))
        events[f"Ladder Go Gym {g}"] = ev(
            [f"set_variable ladder_at:{slug}", f"clear_variable {pick}"],
            [f"is variable_set ladder_at:ladder_town_{g}", f"is variable_set {pick}:{slug}"]
            + open_conds("warrior", g),
        )
        closed_door(events, strings, f"gym_{g}", f"{pick}:{slug}", gym["trainers"][0][1], "warrior", g)
        events[f"Ladder Gym {g} Menu"] = ev(
            ["autosave",
             *choice(["ladder_fight"], pick, back=f"ladder_back_town_{g}", title=f"{slug}_title")],
            menu_idle + [f"is variable_set ladder_at:{slug}"],
        )
        here = [f"is variable_set ladder_at:{slug}", f"is variable_set {pick}:ladder_fight"]
        for t, (sprite, title, team) in enumerate(trainers, 1):
            ts = trainer_slug(g, t)
            strings[ts] = title
            strings[f"{ts}_intro"] = f"Trainer {t} of {len(trainers)}: {title}."
            npcs.append(
                {
                    "slug": ts,
                    "speech": {"profile": {"default": {
                        "pre_battle": None, "post_battle_win": None,
                        "post_battle_lose": None, "post_battle_draw": None,
                    }}},
                    "combat": {},
                    "audio": {},
                    "template": {"sprite_name": sprite, "combat_sheet": sprite, "slug": sprite},
                }
            )
            conds = list(here)
            if t > 1:
                conds.append(f"is battle_outcome player,won,{trainer_slug(g, t - 1)}")
            conds.append(f"not battle_outcome player,won,{ts}")
            # A fresh NPC every try, so its team starts at full health.
            events[f"Ladder Gym {g} Trainer {t}"] = ev(
                [f"clear_variable {pick}", f"set_variable {busy}:yes",
                 "set_environment interior", f"create_npc {ts},{NPC_POS}"]
                + [f"add_monster {m},{lv},{ts}" for m, lv in team]
                + [f"translated_dialog {ts}_intro", f"start_battle player,{ts}",
                   f"remove_npc {ts}", CHECK, f"clear_variable {busy}"],
                conds,
            )
        # The warrior's rung of this town: beating the leader. It runs in the
        # frame after the battle event set CHECK, and holds busy so no menu
        # opens until the announcement is done.
        for t in [len(trainers)]:
            ts = trainer_slug(g, t)
            events[f"Ladder Gym {g} Trainer {t} rank"] = ev(
                [f"set_variable {busy}:yes", f"set_variable ladder_ranked_{ts}:yes"]
                + rank_up("warrior", g) + [f"clear_variable {busy}"],
                ["is variable_set ladder_check_unlock:yes", f"is battle_outcome player,won,{ts}",
                 f"not variable_set ladder_ranked_{ts}"],
            )
        events[f"Ladder Gym {g} Done"] = ev(
            ["translated_dialog ladder_gym_done", f"clear_variable {pick}"],
            here + [f"is battle_outcome player,won,{leader}"],
        )
        unlock_sources[g].append((f"Gym {g}", f"is battle_outcome player,won,{leader}"))

    for t in range(1, len(TOWNS) + 1):
        people_events(events, strings, pick, busy, idle, unlock_sources[t], t)

    # Any one source of town t (its gym leader or any townsperson) opens town
    # t+1 (ladder_stage t -> t+1) and calls the rival. The last town is the
    # summit: there every path satisfied is that path's ending (below). Every
    # unlock name ends in town t's suffix.
    flag = "is variable_set ladder_check_unlock:yes"
    last = len(TOWNS)
    for t, sources in unlock_sources.items():
        if t == last:
            continue
        nxt, s = t + 1, town_suffix(t)
        strings[f"ladder_unlock_{nxt}"] = "New on your map: {1} ({0}), and beyond it the town of {2}!".format(
            *ROUTES[nxt - 1]["name"].split(": ", 1), TOWNS[nxt - 1]["name"])
        # The unlock itself is instant and not gated on idle: it must set the
        # rival's contest before any menu can open (a menu and an idle-gated
        # event can both start in the same frame). The message waits for quiet
        # and for the rival: it is announced once the rival's contest is over
        # (Stephen, 2026-11-25), or at once when the rival is switched off.
        for name, cond in sources:
            kind = "gym" + s if name.startswith("Gym") else name
            events[f"Ladder Unlock {nxt} by {name}"] = ev(
                [f"set_variable ladder_stage:{nxt}", f"set_variable ladder_unlock_msg:{nxt}",
                 f"set_variable ladder_rival_pending:{kind}"],
                [f"is variable_set ladder_stage:{t}", cond],
            )
        for ev_name in [k for k in events if k.startswith(f"Ladder Unlock {nxt} by")]:
            e = events[ev_name]
            e["conditions"].insert(0, flag)
            e["actions"].append("clear_variable ladder_check_unlock")
        events[f"Ladder Unlock {nxt} none"] = ev(
            ["clear_variable ladder_check_unlock"],
            [flag, f"is variable_set ladder_stage:{t}"] + [c.replace("is ", "not ", 1) for _, c in sources],
        )
        events[f"Ladder Unlock {nxt} message"] = ev(
            [f"translated_dialog ladder_unlock_{nxt}", "clear_variable ladder_unlock_msg"],
            idle + [f"is variable_set ladder_unlock_msg:{nxt}", "not variable_set ladder_rival_pending"],
        )
    # The summit's endings: each path once, each with its own message, and the
    # rival challenges after every one (towns 1-5: once per town). The first
    # also sets the last stage (every place on the map). The flag is cleared
    # by "Ladder Unlock already" in the same frame (conditions are all tested
    # before any action runs).
    s = town_suffix(last)
    for name, cond in unlock_sources[last]:
        job = "gym" if name.startswith("Gym") else name.removesuffix(s)
        path = "warrior" if job == "gym" else TOWNS[last - 1]["pupils"][job]["path"]
        ended = f"ladder_end_{path}"
        strings[ended] = ENDINGS[path]
        events[f"Ladder Ending {path}"] = ev(
            [f"set_variable ladder_stage:{last + 1}", f"set_variable {ended}:done",
             f"set_variable ladder_unlock_msg:end_{path}", f"set_variable ladder_rival_pending:{job}{s}"],
            [flag, cond, f"not variable_set {ended}"],
        )
        events[f"Ladder Ending {path} message"] = ev(
            [f"translated_dialog {ended}", "clear_variable ladder_unlock_msg"],
            idle + [f"is variable_set ladder_unlock_msg:end_{path}", "not variable_set ladder_rival_pending"],
        )
    events["Ladder Unlock already"] = ev(
        ["clear_variable ladder_check_unlock"],
        [flag] + [f"not variable_set ladder_stage:{t}" for t in range(1, last)],
    )
    for t in range(1, len(TOWNS) + 1):
        npcs.append(rival_events(events, strings, pick, busy, idle, t))

    split = paginate(events, strings)
    for key, pages in split.items():
        print(f"paged {key}: {len(pages)} pages")
    (ROOT / "maps/ladder_hub.yaml").write_text(
        "# Generated by scripts/ladder/gen.py - edit that, not this.\n"
        + yaml.safe_dump({"events": events}, sort_keys=False, width=200)
    )
    (ROOT / "db/npc/ladder_people.yaml").write_text(
        "# Generated by scripts/ladder/gen.py - edit that, not this.\n"
        + yaml.safe_dump(npcs, sort_keys=False)
    )

    def q(s):
        return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'

    block = "\n".join([BEGIN] + [f"msgid {q(k)}\nmsgstr {q(v)}\n" for k, v in strings.items()] + [END])
    po = PO.read_text()
    if BEGIN in po:
        a, rest = po.split(BEGIN, 1)
        po = a.rstrip("\n") + "\n\n" + block + rest.split(END, 1)[1]
    else:
        po = po.rstrip("\n") + "\n\n" + block + "\n"
    PO.write_text(po)
    print(f"{len(events)} events, {len(npcs)} trainers, {len(strings)} strings")


if __name__ == "__main__":
    build()
