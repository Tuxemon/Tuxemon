import json
from collections import defaultdict
from pathlib import Path

MONSTER_FOLDER = Path.home() / "Tuxemon/mods/tuxemon/db/monster"


def load_monsters(folder: Path):
    monsters = {}
    for file in folder.glob("*.json"):
        with file.open("r", encoding="utf-8") as f:
            data = json.load(f)
            monsters[data["slug"]] = data
    return monsters


def validate_monsters(monsters):
    errors = []
    all_slugs = set(monsters.keys())
    stage_order = {"basic": 0, "stage1": 1, "stage2": 2}

    # Build evolution graph
    graph = defaultdict(list)
    for slug, data in monsters.items():
        for evo in data.get("evolutions", []):
            graph[slug].append(evo["monster_slug"])

    for slug, data in monsters.items():
        # Validate history references
        for entry in data.get("history", []):
            target = entry["slug"]
            if target not in all_slugs:
                errors.append(
                    f"{slug}: history references unknown monster '{target}'"
                )

            for ref in entry.get("evolves_from", []):
                if ref not in all_slugs:
                    errors.append(
                        f"{slug}: evolves_from references unknown monster '{ref}'"
                    )

            for ref in entry.get("evolves_into", []):
                if ref not in all_slugs:
                    errors.append(
                        f"{slug}: evolves_into references unknown monster '{ref}'"
                    )

        # Validate stage progression
        for evo in data.get("evolutions", []):
            target_slug = evo["monster_slug"]
            if target_slug in monsters:
                from_stage = stage_order.get(data.get("stage", "basic"), -1)
                to_stage = stage_order.get(
                    monsters[target_slug].get("stage", "basic"), -1
                )
                if to_stage <= from_stage:
                    errors.append(
                        f"{slug}: evolves into '{target_slug}' with equal or lower stage ({data.get('stage')} → {monsters[target_slug].get('stage')})"
                    )

        # Detect circular evolution
        visited = set()

        def dfs(current, path):
            if current in path:
                cycle = " → ".join(path + [current])
                errors.append(f"{slug}: circular evolution detected: {cycle}")
                return
            if current in visited:
                return  # already checked this path
            visited.add(current)
            path.append(current)
            for next_slug in graph.get(current, []):
                dfs(next_slug, path.copy())

        dfs(slug, [])

    return errors


def main():
    monsters = load_monsters(MONSTER_FOLDER)
    issues = validate_monsters(monsters)

    if issues:
        print("\n Validation Issues Found:")
        for issue in issues:
            print(" -", issue)
    else:
        print("\n All monster files passed validation!")


if __name__ == "__main__":
    main()
