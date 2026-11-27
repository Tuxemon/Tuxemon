# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from tuxemon.database.runtime import db
from tuxemon.db import ElementModel
from tuxemon.element import Element
from tuxemon.states.phone_field_notes import all_elements


def test_all_elements_lists_every_element_even_after_one_was_loaded():
    saved = db.database.get("element")
    db.database["element"] = {
        slug: ElementModel(
            slug=slug, icon=f"gfx/ui/icons/element/{slug}_type.png", types=[]
        )
        for slug in ("fire", "metal", "normal")
    }
    try:
        Element.clear_cache()
        Element.get("fire")  # a partly filled cache used to hide the rest
        assert set(all_elements()) == {"fire", "metal", "normal"}
    finally:
        Element.clear_cache()
        if saved is not None:
            db.database["element"] = saved
