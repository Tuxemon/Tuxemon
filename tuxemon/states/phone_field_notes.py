# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""
NuPhone "Field notes" app: what the player has learned about battle rules.

Four pages:

* Type chart: a grid of attack type x defending type, filled in only where
  the player has seen that matchup. Types the player has not met at all
  (no seen monster or matchup of that type) show as "?".
* Type matchups: the same, as a list with words (combat/field_notes.py).
* Attack ranges: each range is explained once the player has seen it used.
* Stats: what HP, Melee, Armour, Dodge... and move Accuracy/Potency mean.
"""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Any, ClassVar

import pygame
from pygame.surface import Surface
from pygame_menu.locals import ALIGN_CENTER, POSITION_EAST
from pygame_menu.menu import Menu

from tuxemon.combat.field_notes import known_matchups, known_ranges
from tuxemon.constants.asset_loader import fetch_asset
from tuxemon.database.runtime import db
from tuxemon.db import MonsterModel
from tuxemon.element import Element
from tuxemon.graphics import load_image
from tuxemon.locale.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.platform.const.graphics import BG_PHONE
from tuxemon.tools import open_dialog
from tuxemon.user_config import CONFIG

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.entity.npc import NPC

# Damaging ranges, in the order they are listed ("special" deals no damage).
RANGES = ["melee", "touch", "ranged", "reach", "reliable"]
STATS = [
    "hp",
    "melee",
    "ranged",
    "armour",
    "dodge",
    "speed",
    "accuracy",
    "potency",
]
LINES_PER_PAGE = 3
# Show types the player hasn't met as "?" rows/columns (True), or leave them
# out entirely so a new type is a surprise (False).
SHOW_UNMET_TYPES = True
# Cell colours of the chart: double, half, none, normal, unknown.
CELL_COLOURS = {
    "double": (88, 160, 88),
    "half": (196, 112, 88),
    "none": (60, 60, 60),
    "normal": (200, 200, 200),
    "unknown": (235, 235, 235),
}


def all_elements() -> dict[str, Element]:
    """Every element in the database. (Element.get_all_elements() returns only
    those loaded so far once any is loaded, so load the rest first.)"""
    Element.load_all_elements()
    return Element.get_all_elements()


def effect_text(multiplier: float) -> str:
    """Words for a type multiplier: 2 -> 'double damage'."""
    words = {2.0: "double", 0.5: "half", 1.0: "normal", 0.0: "none"}
    key = words.get(multiplier)
    if key is None:
        return T.format(
            "field_notes_effect_other", {"mult": f"{multiplier:g}"}
        )
    return T.translate(f"field_notes_effect_{key}")


def type_lines(character: NPC, attack: str) -> list[str]:
    """Dialog lines for one attack type: its known matchups, then what's left."""
    elements = all_elements()
    attacker = elements[attack]
    known = sorted(d for a, d in known_matchups(character) if a == attack)
    lines = [
        T.format(
            "field_notes_vs",
            {
                "attack": attacker.name,
                "defend": elements[d].name if d in elements else d,
                "effect": effect_text(attacker.lookup_multiplier(d)),
            },
        )
        for d in known
    ]
    missing = len(elements) - len(known)
    if not known:
        lines.append(
            T.format("field_notes_type_none", {"type": attacker.name})
        )
    elif missing:
        lines.append(
            T.format(
                "field_notes_not_seen",
                {"count": missing, "type": attacker.name},
            )
        )
    return lines


def met_types(character: NPC) -> set[str]:
    """Types the player has met: in a seen matchup, or of a monster in the
    player's Tuxepedia (seen or caught)."""
    met = {t for pair in known_matchups(character) for t in pair}
    for slug in character.tuxepedia.get_monsters():
        try:
            met.update(MonsterModel.lookup(slug, db).types)
        except Exception:
            continue
    return met


def cell_text(multiplier: float) -> tuple[str, str]:
    """(text, colour key) for a known chart cell."""
    if multiplier == 0:
        return "0", "none"
    if multiplier > 1:
        return f"{multiplier:g}x", "double"
    if multiplier < 1:
        return "1/2" if multiplier == 0.5 else f"{multiplier:g}x", "half"
    return "1", "normal"


def type_order(elements: dict[str, Element], met: set[str]) -> list[str]:
    """Met types by name, then unmet ones (by slug) at the end, so a "?"
    row's position doesn't hint at its name. Unmet are dropped entirely
    when SHOW_UNMET_TYPES is False."""
    shown = sorted(
        (s for s in elements if s in met), key=lambda s: elements[s].name
    )
    if SHOW_UNMET_TYPES:
        shown += sorted(s for s in elements if s not in met)
    return shown


def chart_surface(character: NPC, cell: int) -> Surface:
    """Draw the type chart: rows attack, columns defend, `cell` px squares."""
    elements = all_elements()
    met = met_types(character)
    slugs = type_order(elements, met)
    known = known_matchups(character)
    font = pygame.font.Font(
        fetch_asset("font", CONFIG.locale.font_file), cell // 3
    )
    n = len(slugs)
    surf = Surface(((n + 1) * cell, (n + 1) * cell), pygame.SRCALPHA)

    def header(slug: str, x: int, y: int) -> None:
        rect = pygame.Rect(x, y, cell, cell)
        if slug in met and elements[slug].icon:
            icon = pygame.transform.scale(
                load_image(elements[slug].icon), (cell - 4, cell - 4)
            )
            surf.blit(icon, (x + 2, y + 2))
        else:
            text = font.render("?", True, (0, 0, 0))
            surf.blit(text, text.get_rect(center=rect.center))

    corner = font.render("A\\D", True, (0, 0, 0))
    surf.blit(corner, corner.get_rect(center=(cell // 2, cell // 2)))
    for i, slug in enumerate(slugs, 1):
        header(slug, i * cell, 0)  # defending types across the top
        header(slug, 0, i * cell)  # attack types down the side
    for row, attack in enumerate(slugs, 1):
        for col, defend in enumerate(slugs, 1):
            rect = pygame.Rect(col * cell, row * cell, cell, cell)
            if (attack, defend) in known:
                label, colour = cell_text(
                    elements[attack].lookup_multiplier(defend)
                )
            else:
                label, colour = "?", "unknown"
            pygame.draw.rect(surf, CELL_COLOURS[colour], rect.inflate(-2, -2))
            text = font.render(
                label, True, (255, 255, 255) if colour == "none" else (0, 0, 0)
            )
            surf.blit(text, text.get_rect(center=rect.center))
    return surf


def pages(lines: list[str]) -> list[str]:
    """Group dialog lines a few at a time, one group per dialog page."""
    return [
        "\n".join(lines[i : i + LINES_PER_PAGE])
        for i in range(0, len(lines), LINES_PER_PAGE)
    ]


class NuPhoneFieldNotes(PygameMenuState):
    name: ClassVar[str] = "NuPhoneFieldNotes"

    def say(self, lines: list[str]) -> None:
        open_dialog(self.client, pages(lines), dialog_speed="max")

    def open_page(self, page: str) -> None:
        self.client.push_state(self.name, character=self.char, page=page)

    def add_menu_items(self, menu: Menu) -> None:
        big = self.font_type.medium

        if self.page == "chart":
            width, height = self.client.context.resolution
            n = len(all_elements()) + 1
            cell = int(min(width * 0.8, height * 0.8) // n)
            menu.add.surface(chart_surface(self.char, cell))
            menu.set_title(T.translate("field_notes_chart"))

        elif self.page == "types":
            known = known_matchups(self.char)
            elements = all_elements()
            met = met_types(self.char)
            for slug in type_order(elements, met):
                element = elements[slug]
                if slug not in met:
                    # same rule as the chart: unmet types are "???" or hidden
                    if SHOW_UNMET_TYPES:
                        menu.add.button(
                            title=T.translate("field_notes_unknown"),
                            action=partial(
                                self.say,
                                [T.translate("field_notes_type_unmet")],
                            ),
                            font_size=big,
                        )
                    continue
                n = sum(1 for a, _ in known if a == slug)
                title = T.format(
                    "field_notes_type_button",
                    {"type": element.name, "known": n, "total": len(elements)},
                )
                menu.add.button(
                    title=title,
                    action=partial(self.say, type_lines(self.char, slug)),
                    font_size=big,
                )
            menu.set_title(T.translate("field_notes_types"))

        elif self.page == "ranges":
            ranges = known_ranges(self.char)
            for r in RANGES:
                seen = r in ranges
                menu.add.button(
                    title=T.translate(f"field_notes_range_{r}_name")
                    if seen
                    else T.translate("field_notes_unknown"),
                    action=partial(
                        self.say,
                        [
                            T.translate(f"field_notes_range_{r}")
                            if seen
                            else T.translate("field_notes_range_unseen")
                        ],
                    ),
                    font_size=big,
                )
            menu.set_title(T.translate("field_notes_ranges"))

        elif self.page == "stats":
            for s in STATS:
                menu.add.button(
                    title=T.translate(f"field_notes_stat_{s}_name"),
                    action=partial(
                        self.say, [T.translate(f"field_notes_stat_{s}")]
                    ),
                    font_size=big,
                )
            menu.set_title(T.translate("field_notes_stats"))

        else:
            for page in ("chart", "types", "ranges", "stats"):
                menu.add.button(
                    title=T.translate(f"field_notes_{page}"),
                    action=partial(self.open_page, page),
                    font_size=big,
                )
                menu.add.vertical_margin(25)
            menu.set_title(T.translate("app_field_notes"))
        menu.center_content()

    def __init__(
        self,
        client: BaseClient,
        character: NPC,
        page: str = "index",
        **kwargs: Any,
    ) -> None:
        self.char = character
        self.page = page
        width, height = client.context.resolution

        super().__init__(client=client, height=height, width=width, **kwargs)

        theme = self._setup_theme(BG_PHONE)
        theme.scrollarea_position = POSITION_EAST
        theme.widget_alignment = ALIGN_CENTER
        theme.title = True
        self._menu_config["theme"] = theme

        self.add_menu_items(self.menu)
        self.reset_theme()
