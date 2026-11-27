"""Check the Ladder's tables and generated files without starting the game.

Run from the repo root:  .venv/bin/python scripts/ladder/check_world.py
Exit 0 = clean; otherwise every problem is printed, one per line.

Checks:
1. every species with txmn_id > 0 is in exactly one route area, and nothing else is;
2. every area's encounter file exists and matches the table (gen.py has run);
3. every environment is in db/environment, every NPC sprite in db/template;
4. areas hold 6-10 species, keys are unique per route, the last one is the rarest;
5. route levels; route N holds a counter to gym N's type;
6. every monster named in gen.py exists; the bars (pupils, the rival's bets)
   are passable by a lone level-5 starter.
"""

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
import gen  # noqa: E402
from world import ROUTES, SPARE_AREAS  # noqa: E402

ROOT = Path("mods/tuxemon")
LEVELS = [(3, 6), (4, 7), (5, 8), (6, 9), (7, 10), (8, 11)]
# A lone level-5 starter, measured 2026-11-25 (300 spawns each, minimum over
# agnite, squink, budaye): melee 43, speed 65, weight 18.0 kg; Tuxepedia
# height (the species') 70 cm.
STARTER_MIN = {"melee": 43, "speed": 65, "weight": 18.0, "height_cm": 70}
problems = []


def bad(msg):
    problems.append(msg)
    print("FAIL", msg)


def main():
    ms = {}
    for f in sorted((ROOT / "db/monster").glob("*.yaml")):
        d = yaml.safe_load(f.read_text())
        ms[d["slug"]] = d
    numbered = {s for s, d in ms.items() if d.get("txmn_id", 0) > 0}
    envs = {f.stem for f in (ROOT / "db/environment").glob("*.yaml")}
    templates = {t["slug"] for t in yaml.safe_load((ROOT / "db/template/template.yaml").read_text())}

    # 1. every species exactly once, on a route or in a spare area kept for
    #    later routes; a route has two to four areas
    where = {}
    for n, route in enumerate(ROUTES, 1):
        if not 2 <= len(route["areas"]) <= 4:
            bad(f"route {n} has {len(route['areas'])} areas (two to four wanted)")
        for a in route["areas"]:
            for m in a["monsters"]:
                where.setdefault(m, []).append(f"route {n} {a['key']}")
    on_routes = len(where)
    for n, areas in SPARE_AREAS.items():
        for a in areas:
            for m in a["monsters"]:
                where.setdefault(m, []).append(f"spare (was route {n}) {a['key']}")
    for m, places in sorted(where.items()):
        if len(places) > 1:
            bad(f"{m} is placed {len(places)} times: {places}")
        if m not in numbered:
            bad(f"{m} ({places[0]}) is not a species with a txmn_id")
    for m in sorted(numbered - set(where)):
        bad(f"{m} is on no route and in no spare area")

    if len(ROUTES) != len(gen.TOWNS):
        bad(f"{len(ROUTES)} routes for {len(gen.TOWNS)} towns")
    for n, route in enumerate(ROUTES, 1):
        # 5. levels
        # (wild levels are 1-2 everywhere for now; the planned spread waits in levels_later)
        lo, hi = route["levels"]
        if not 1 <= lo <= hi:
            bad(f"route {n} levels {route['levels']} are not a valid range")
        if n <= len(LEVELS) and tuple(route.get("levels_later", route["levels"])) != LEVELS[n - 1]:
            bad(f"route {n} planned levels {route.get('levels_later')}, want {LEVELS[n - 1]}")
        keys = [a["key"] for a in route["areas"]]
        if len(keys) != len(set(keys)):
            bad(f"route {n} repeats an area key: {keys}")
        for a in route["areas"]:
            where_ = f"route {n} {a['key']}"
            # 3. environment
            if a["environment"] not in envs:
                bad(f"{where_}: environment {a['environment']!r} is not in db/environment")
            # 4. size, rare last, text
            k = len(a["monsters"])
            if not 6 <= k <= 10:
                bad(f"{where_}: {k} species (want 6-10)")
            w = list(a["monsters"].values())
            if not all(x > w[-1] for x in w[:-1]):
                bad(f"{where_}: the last monster is not the single rarest {w}")
            if not a.get("label") or not a.get("hint"):
                bad(f"{where_}: no label or hint")
            # 2. encounter file
            f = ROOT / f"db/encounter/ladder_route_{n}_{a['key']}.yaml"
            if not f.exists():
                bad(f"{where_}: no encounter file {f}")
                continue
            table = yaml.safe_load(f.read_text())
            got = {e["monster"]: e["encounter_rate"] for e in table["monsters"]}
            if got != dict(a["monsters"]):
                bad(f"{where_}: {f} does not match world.py (run gen.py)")
            if any(e["level_range"] != list(route["levels"]) for e in table["monsters"]):
                bad(f"{where_}: {f} levels differ from the route's")
        # 5. a counter to gym n
        weak = set(gen.weak_to(gen.GYM_TYPES[n - 1]))
        if not any(weak & set(ms[m]["types"]) for a in route["areas"] for m in a["monsters"] if m in ms):
            bad(f"route {n} has no monster that beats gym {n}'s {gen.GYM_TYPES[n - 1]}")
    encounters = {f.stem for f in (ROOT / "db/encounter").glob("ladder_route_*.yaml")}
    wanted = {f"ladder_route_{n}_{a['key']}" for n, r in enumerate(ROUTES, 1) for a in r["areas"]}
    for stale in sorted(encounters - wanted):
        bad(f"stale encounter file {stale}.yaml (no area in world.py)")

    # 3. NPC sprites (the generated file and the tables)
    for npc in yaml.safe_load((ROOT / "db/npc/ladder_people.yaml").read_text()):
        for key in ("sprite_name", "combat_sheet", "slug"):
            if npc["template"][key] not in templates:
                bad(f"npc {npc['slug']}: template {key} {npc['template'][key]!r} is not in template.yaml")
    sprites = [t[0] for g in gen.GYMS for t in g["trainers"]] + [gen.RIVAL["sprite"]]
    for sp in sprites:
        if sp not in templates:
            bad(f"sprite {sp!r} is not in template.yaml")
        # the db's own checks (NpcTemplateModel): a walking sheet or a static
        # prop, and a combat sheet; a template slug alone is not enough
        if not ((ROOT / f"sprites/{sp}.png").exists() or (ROOT / f"sprites_obj/{sp}.png").exists()):
            bad(f"sprite {sp!r}: no sprites/{sp}.png or sprites_obj/{sp}.png")
        if not (ROOT / f"gfx/sprites/player/{sp}.png").exists():
            bad(f"sprite {sp!r}: no combat sheet gfx/sprites/player/{sp}.png")

    # 6. monsters named in gen.py exist; bars are passable
    named = [m for g in gen.GYMS for t in g["trainers"] for m, _ in t[2]] + gen.STARTERS
    named += [t["breeder"]["monster"] for t in gen.TOWNS if "monster" in t["breeder"]]
    named += [m for row in gen.RIVAL["bets"] for m, _ in row.values()]
    for m in named:
        if m not in ms:
            bad(f"gen.py names {m!r}, which is not in db/monster")
    for n, g in enumerate(gen.GYMS, 1):
        levels = [max(lv for _, lv in t[2]) for t in g["trainers"]]
        if n < len(gen.GYMS) and levels != [n + 1, n + 1, n + 2, n + 3]:
            bad(f"gym {n} levels {levels}, want {[n + 1, n + 1, n + 2, n + 3]}")
        if any(len(t[2]) != 1 for t in g["trainers"][:-1]) or (n < len(gen.GYMS) and len(g["trainers"][-1][2]) != 1):
            bad(f"gym {n}: a trainer has more than one monster")
    boss = gen.GYMS[-1]["trainers"][-1][2]
    if len(boss) != 6 or any(lv != 6 for _, lv in boss):
        bad(f"the boss should have six monsters at level 6: {boss}")
    if len(gen.RIVAL["bets"]) != len(gen.TOWNS):
        bad(f"RIVAL['bets'] has {len(gen.RIVAL['bets'])} rows for {len(gen.TOWNS)} towns")
    for n, row in enumerate(gen.RIVAL["bets"], 1):
        (tall, cm), (heavy, kg) = row["tall"], row["heavy"]
        if cm >= STARTER_MIN["height_cm"]:
            bad(f"town {n}: Rex's {tall} at {cm} cm is not beaten by every starter")
        if kg > STARTER_MIN["weight"]:
            bad(f"town {n}: Rex's {heavy} at {kg} kg outweighs a starter")
        if n > 2 and (ms[tall]["height"] != cm or ms[heavy]["weight"] != kg):
            bad(f"town {n}: Rex's numbers differ from the db ({tall} {ms[tall]['height']} cm, "
                f"{heavy} {ms[heavy]['weight']} kg)")
    for n, t in enumerate(gen.TOWNS, 1):
        for job, p in t["pupils"].items():
            if p["kind"] == "seen" and p["bar_cm"] >= STARTER_MIN["height_cm"]:
                bad(f"town {n} {job} pupil: {p['bar_cm']} cm is not beaten by every starter")
            if p["kind"] in ("team", "race") and p["bar"] > STARTER_MIN[p["stat"]]:
                bad(f"town {n} {job} pupil: {p['stat']} {p['bar']} is above a lone starter's")
    for path, titles in gen.PATHS.items():
        if len(titles) != len(gen.TOWNS):
            bad(f"{path} has {len(titles)} titles for {len(gen.TOWNS)} towns")

    # information only: an evolved form on an earlier route than its base
    route_of = {m: n for n, r in enumerate(ROUTES, 1) for a in r["areas"] for m in a["monsters"]}
    early = []
    for m, n in route_of.items():
        for h in ms[m].get("history") or []:
            if h["slug"] in route_of and m in (h.get("evolves_into") or []) and route_of[h["slug"]] > n:
                early.append(f"{m} (route {n}) before {h['slug']} (route {route_of[h['slug']]})")
    print(f"info: {len(early)} evolved forms sit on an earlier route than the form they evolve from")
    print(f"{on_routes} species on {sum(len(r['areas']) for r in ROUTES)} areas of {len(ROUTES)} routes, "
          f"{len(where) - on_routes} waiting in {sum(len(a) for a in SPARE_AREAS.values())} spare areas; "
          f"{len(problems)} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
