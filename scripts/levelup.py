"""
Increase the level of all trainer monsters in a map by a specified amount.

Handles both TMX files (inline XML event properties) and companion YAML files
(same basename, e.g. mymap.yaml alongside mymap.tmx).

USAGE

    python scripts/levelup.py <map_file.tmx> <levels>

EXAMPLES

    python scripts/levelup.py mods/tuxemon/maps/spyder_nimrod_middle.tmx 5
    python scripts/levelup.py mods/tuxemon/maps/eclipse_lion_mountain_high.tmx 10

Modifies files in place. If a companion YAML file exists for the map, both
the TMX and the YAML are updated. Levels are clamped to a minimum of 1.
"""

import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]

ADD_MONSTER_RE = re.compile(
    r"^(add_monster\s+[^,]+,)(\d+)((?:,.*)?)$"
)


def bump_level(action: str, delta: int) -> tuple[str, bool]:
    """Return (updated_action, changed). Level is clamped to minimum 1."""
    m = ADD_MONSTER_RE.match(action.strip())
    if not m:
        return action, False
    new_level = max(1, int(m.group(2)) + delta)
    return f"{m.group(1)}{new_level}{m.group(3)}", True


# ---------------------------------------------------------------------------
# TMX (XML) handling
# ---------------------------------------------------------------------------

def update_tmx(tmx_path: Path, delta: int) -> int:
    """Edit add_monster levels in TMX properties in place. Returns change count."""
    text = tmx_path.read_text(encoding="utf-8")
    changes = 0

    def replace_value(m: re.Match) -> str:
        nonlocal changes
        new_val, changed = bump_level(m.group(2), delta)
        if changed:
            changes += 1
        return f'{m.group(1)}{new_val}{m.group(3)}'

    # Match: value="add_monster ..." inside a property tag
    prop_re = re.compile(
        r'(value=")(add_monster\s+[^"]+)(")',
        re.IGNORECASE,
    )
    new_text = prop_re.sub(replace_value, text)
    if new_text != text:
        tmx_path.write_text(new_text, encoding="utf-8")
    return changes


# ---------------------------------------------------------------------------
# YAML handling
# ---------------------------------------------------------------------------

def update_yaml(yaml_path: Path, delta: int) -> int:
    """Edit add_monster levels in a companion YAML file in place. Returns change count."""
    if yaml is None:
        print(
            f"WARNING: PyYAML not available; skipping {yaml_path}. "
            "Install it with: pip install pyyaml"
        )
        return 0

    text = yaml_path.read_text(encoding="utf-8")
    changes = 0

    # Process line-by-line to preserve formatting as much as possible
    lines = text.splitlines(keepends=True)
    new_lines = []
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("- add_monster"):
            indent = line[: len(line) - len(stripped)]
            action = stripped[2:].rstrip("\n\r")  # strip leading "- "
            new_action, changed = bump_level(action, delta)
            if changed:
                changes += 1
            new_lines.append(f"{indent}- {new_action}\n")
        else:
            new_lines.append(line)

    new_text = "".join(new_lines)
    if new_text != text:
        yaml_path.write_text(new_text, encoding="utf-8")
    return changes


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

MAPS_DIR = Path(__file__).parent.parent / "mods" / "tuxemon" / "maps"


def main() -> None:
    if len(sys.argv) != 3:
        print("Usage: python levelup.py <map_name.tmx> <levels>")
        print("Example: python levelup.py spyder_nimrod_middle.tmx 5")
        sys.exit(1)

    tmx_path = MAPS_DIR / sys.argv[1]
    if not tmx_path.exists():
        print(f"Error: file not found: {tmx_path}")
        sys.exit(1)
    if tmx_path.suffix.lower() != ".tmx":
        print(f"Error: expected a .tmx file, got: {tmx_path}")
        sys.exit(1)

    try:
        delta = int(sys.argv[2])
    except ValueError:
        print(f"Error: levels must be an integer, got: {sys.argv[2]!r}")
        sys.exit(1)

    total = 0

    # Update TMX
    tmx_changes = update_tmx(tmx_path, delta)
    total += tmx_changes
    if tmx_changes:
        print(f"TMX:  updated {tmx_changes} add_monster action(s) in {tmx_path}")
    else:
        print(f"TMX:  no add_monster actions found in {tmx_path}")

    # Update companion YAML if present
    yaml_path = tmx_path.with_suffix(".yaml")
    if yaml_path.exists():
        yaml_changes = update_yaml(yaml_path, delta)
        total += yaml_changes
        if yaml_changes:
            print(f"YAML: updated {yaml_changes} add_monster action(s) in {yaml_path}")
        else:
            print(f"YAML: no add_monster actions found in {yaml_path}")
    else:
        print(f"YAML: no companion file at {yaml_path}, skipping")

    print(f"\nDone. {total} monster level(s) {'increased' if delta >= 0 else 'decreased'} by {abs(delta)}.")


if __name__ == "__main__":
    main()