#!/usr/bin/env python3
"""
Cheat script: add every monster in the database to monster storage boxes.

Usage:
    python scripts/cheat_all_monsters.py --slot SLOT [--level LEVEL]

Run from the Tuxemon root directory. The game must NOT be running.
"""

import argparse
import json
import sys
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
MON_DB_DIR = REPO_ROOT / "mods" / "tuxemon" / "db" / "monster"


def find_save_path(slot: int) -> Path:
    """Locate the save file for a given slot, supporting json/yaml/cbor."""
    if sys.platform == "win32":
        base = Path.home() / ".tuxemon" / "saves"
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support" / "tuxemon" / "saves"
    else:
        base = Path.home() / ".tuxemon" / "saves"

    for ext in ("save", "json", "yaml", "cbor"):
        p = base / f"slot{slot}.{ext}"
        if p.exists():
            return p
        # compressed variants
        for comp in ("gz", "bz2", "lzma"):
            p = base / f"slot{slot}.c{ext}.{comp}"
            if p.exists():
                return p

    raise FileNotFoundError(
        f"No save file found for slot {slot} in {base}\n"
        "Start a new game, save once, then re-run this script."
    )


def load_save(path: Path) -> dict:
    suffix = path.suffix.lower()
    text = path.read_text(encoding="utf-8")
    if suffix in (".json", ".save"):
        return json.loads(text)
    if suffix in (".yaml", ".yml"):
        import yaml
        return yaml.safe_load(text)
    raise ValueError(f"Unsupported save format: {path}")


def write_save(data: dict, path: Path) -> None:
    suffix = path.suffix.lower()
    if suffix in (".json", ".save"):
        path.write_text(json.dumps(data, indent=4), encoding="utf-8")
    elif suffix in (".yaml", ".yml"):
        import yaml
        path.write_text(yaml.dump(data, allow_unicode=True), encoding="utf-8")
    else:
        raise ValueError(f"Unsupported save format: {path}")


def make_monster_dict(slug: str, level: int) -> dict:
    """Build a minimal monster save dict without importing the game."""
    return {
        "slug": slug,
        "instance_id": uuid.uuid4().hex,
        "level": level,
        "total_experience": 0,
        "exp_group_slug": "default",
        "current_hp": 50,
        "steps": 0,
        "name": None,
        "birthdate": None,
        "capture_date": None,
        "capture_device": None,
        "height": None,
        "weight": None,
        "taste_cold": None,
        "taste_warm": None,
        "gender": "neuter",
        "acquisition": "captured",
        "plague": {},
        "mother_iid": None,
        "father_iid": None,
        "body": {},
        "status": [],
        "moves": [],
        "held_item": None,
        "training_points": {},
        "individual_values": {},
        "modifiers": {},
        "bond_dict": {},
        "flair_slugs": [],
        "flairs": {},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Add all monsters to a save file.")
    parser.add_argument("--slot", type=int, required=True, help="Save slot number")
    parser.add_argument("--level", type=int, default=5, help="Monster level (default: 5)")
    args = parser.parse_args()

    try:
        save_path = find_save_path(args.slot)
    except FileNotFoundError as e:
        print(e)
        sys.exit(1)

    print(f"Loading save: {save_path}")
    save_data = load_save(save_path)

    npc_state = save_data.get("npc_state") or {}

    # Collect slugs already present so we don't duplicate.
    existing: set[str] = set()
    for m in npc_state.get("monsters", []):
        existing.add(m["slug"])
    for box in npc_state.get("monster_boxes", {}).values():
        for m in box:
            existing.add(m["slug"])

    # Read all slugs from the YAML files (no game imports needed).
    all_slugs = sorted(p.stem for p in MON_DB_DIR.glob("*.yaml"))
    print(f"Found {len(all_slugs)} monsters in the database.")

    # --- Boxes ---
    new_monsters = [
        make_monster_dict(slug, args.level)
        for slug in all_slugs
        if slug not in existing
    ]
    if new_monsters:
        print(f"Adding {len(new_monsters)} monsters to storage ({len(all_slugs) - len(new_monsters)} already present).")
        BOX_SIZE = 30
        boxes: dict = dict(npc_state.get("monster_boxes", {}))
        idx = 1
        while f"cheat_box_{idx}" in boxes:
            idx += 1
        for i in range(0, len(new_monsters), BOX_SIZE):
            key = f"cheat_box_{idx}"
            chunk = new_monsters[i : i + BOX_SIZE]
            boxes[key] = chunk
            print(f"  Created {key!r} with {len(chunk)} monsters.")
            idx += 1
        npc_state["monster_boxes"] = boxes
    else:
        print("All monsters already in storage, skipping box update.")

    # --- Tuxepedia ---
    tuxepedia: dict = dict(npc_state.get("tuxepedia") or {})
    needs_update = [s for s in all_slugs if tuxepedia.get(s, {}).get("status") != "caught"]
    if needs_update:
        print(f"Marking {len(needs_update)} monsters as caught in tuxepedia.")
        for slug in all_slugs:
            entry = tuxepedia.get(slug, {})
            tuxepedia[slug] = {
                "status": "caught",
                "appearance_count": max(entry.get("appearance_count", 0), 1),
                "caught_count": max(entry.get("caught_count", 0), 1),
            }
        npc_state["tuxepedia"] = tuxepedia
    else:
        print("Tuxepedia already up to date.")

    save_data["npc_state"] = npc_state

    write_save(save_data, save_path)
    print(f"Done! Save written to {save_path}")


if __name__ == "__main__":
    main()