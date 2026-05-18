# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, ClassVar

from pygame_menu.locals import ALIGN_CENTER, ALIGN_LEFT, POSITION_EAST
from pygame_menu.menu import Menu

from tuxemon import formula
from tuxemon.database.runtime import db
from tuxemon.db import MonsterModel
from tuxemon.locale.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.monster.sprite import MonsterSpriteHandler, SpriteLoader
from tuxemon.platform.const import buttons
from tuxemon.platform.const.graphics import BG_JOURNAL_INFO
from tuxemon.platform.const.sizes import U_CM, U_FT, U_KG, U_LB
from tuxemon.tools import fix_measure

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.entity.npc import NPC
    from tuxemon.platform.events import PlayerInput

lookup_cache: dict[str, MonsterModel] = {}


def _lookup_monsters() -> None:
    global lookup_cache
    lookup_cache = {
        mon_name: result
        for mon_name in db.database["monster"]
        if (result := MonsterModel.lookup(mon_name, db)).txmn_id > 0
    }


class JournalInfoState(PygameMenuState):
    """Shows journal (screen 3/3)."""

    name: ClassVar[str] = "JournalInfoState"

    def add_menu_items(self, menu: Menu, monster: MonsterModel) -> None:
        def fxw(r: float) -> int:
            return fix_measure(menu._width, r)

        def fxh(r: float) -> int:
            return fix_measure(menu._height, r)

        menu._width = fxw(248 / 256)

        # evolutions
        evo = T.translate("no_evolution")
        if monster.evolutions:
            evo = T.translate(
                "yes_evolution"
                if len(monster.evolutions) == 1
                else "yes_evolutions"
            )
        # types
        types = " ".join(map(lambda s: T.translate(s), monster.types))
        # weight and height
        unit = self.client.config.unit_measure
        if unit == "metric":
            mon_weight = round(monster.weight, 1)
            mon_height = round(monster.height, 1)
            unit_weight = U_KG
            unit_height = U_CM
        else:
            mon_weight = formula.convert_lbs(monster.weight)
            mon_height = formula.convert_ft(monster.height)
            unit_weight = U_LB
            unit_height = U_FT
        # name
        menu._auto_centering = False
        name = T.translate(monster.slug).upper()
        lab1: Any = menu.add.label(
            title=name,
            label_id="name",
            font_size=self.font_type.biggest,
            align=ALIGN_LEFT,
            float=True,
        )
        lab1.translate(fxw(126 / 256), fxh(19.8 / 144))
        # weight
        _weight = f"{mon_weight} {unit_weight}"
        lab2: Any = menu.add.label(
            title=_weight,
            label_id="weight",
            font_size=self.font_type.small,
            align=ALIGN_LEFT,
            float=True,
        )
        lab2.translate(fxw(158 / 256), fxh(39 / 144))
        # height
        _height = f"{mon_height} {unit_height}"
        lab3: Any = menu.add.label(
            title=_height,
            label_id="height",
            font_size=self.font_type.small,
            align=ALIGN_LEFT,
            float=True,
        )
        lab3.translate(fxw(126 / 256), fxh(39 / 144))
        # type
        path1 = f"gfx/ui/icons/element/{monster.types[0]}_type_small.png"
        type_image_1 = self._create_image(path1)
        type_image_1.scale(self.factor, self.factor)
        if len(monster.types) > 1:
            path2 = f"gfx/ui/icons/element/{monster.types[1]}_type_small.png"
            type_image_2 = self._create_image(path2)
            type_image_2.scale(self.factor, self.factor)
            menu.add.image(type_image_1, float=True).translate(
                fxw(11.4 / 256), fxh(47.8 / 144)
            )
            menu.add.image(type_image_2, float=True).translate(
                fxw(25.4 / 256), fxh(47.8 / 144)
            )
        else:
            menu.add.image(type_image_1, float=True).translate(
                fxw(11.4 / 256), fxh(47.8 / 144)
            )

        # Shift amount for two types
        type_shift = (15 / 256) if len(monster.types) > 1 else 0

        types = self._safe_display(types)
        lab5: Any = menu.add.label(
            title=types,
            label_id="type_loaded",
            font_size=self.font_type.small,
            align=ALIGN_LEFT,
            float=True,
        )
        lab5.translate(fxw((141.4 / 256) + type_shift), fxh(56 / 144))

        _type = T.translate("monster_menu_type")
        lab4: Any = menu.add.label(
            title=_type,
            label_id="type_label",
            font_size=self.font_type.small,
            align=ALIGN_LEFT,
            float=True,
        )
        lab4.translate(fxw((141 / 256) + type_shift), fxh(49 / 144))
        # shape
        menu_shape = T.translate("monster_menu_shape")
        _shape = T.translate(monster.shape)
        shape = f"{menu_shape}: {_shape}"
        lab6: Any = menu.add.label(
            title=shape,
            label_id="shape",
            font_size=self.font_type.small,
            align=ALIGN_LEFT,
            float=True,
        )
        lab6.translate(fxw(126 / 256), fxh(66 / 144))
        # species
        spec = T.translate(f"cat_{monster.species}")
        spec = self._safe_display(spec)
        species = spec + " " + T.translate("monster_menu_species")
        lab7: Any = menu.add.label(
            title=species,
            label_id="species",
            font_size=self.font_type.small,
            align=ALIGN_LEFT,
            float=True,
        )
        lab7.translate(fxw(126 / 256), fxh(29 / 144))
        # txmn_id
        _txmn_id = f"ID: {monster.txmn_id}"
        lab8: Any = menu.add.label(
            title=_txmn_id,
            label_id="txmn_id",
            font_size=self.font_type.small,
            align=ALIGN_LEFT,
            float=True,
        )
        lab8.translate(fxw(124.6 / 256), fxh(10 / 144))

        # description
        desc = T.translate(f"{monster.slug}_description")
        desc = self._safe_display(desc)
        lab9: Any = menu.add.label(
            title=desc,
            label_id="description",
            font_size=self.font_type.small,
            wordwrap=True,
            leading=35,
            align=ALIGN_LEFT,
            float=True,
        )

        lab9.translate(fxw(2 / 256), fxh(82 / 144))

        # evolution
        evo = self._safe_display(evo)
        lab10: Any = menu.add.label(
            title=evo,
            label_id="evolution",
            font_size=self.font_type.small,
            wordwrap=True,
            align=ALIGN_LEFT,
            float=True,
        )
        lab10.translate(fxw(2 / 256), fxh(109 / 144))

        # evolution monsters
        if self.is_visible:
            f = menu.add.frame_h(
                float=True,
                width=fxw(243 / 256),
                height=fxw(7 / 144),
                frame_id="histories",
            )
            f.translate(fxw(5 / 256), fxh(115 / 144))
            f._relax = True
            slugs = [ele.monster_slug for ele in monster.evolutions]
            elements = list(dict.fromkeys(slugs))
            labels = [
                menu.add.label(
                    title=f"{T.translate(ele).upper()}",
                    align=ALIGN_LEFT,
                    font_size=self.font_type.smaller,
                )
                for ele in elements
            ]
            for elements in labels:
                f.pack(elements)
        # image
        loader = SpriteLoader()
        sprites = monster.sprites
        assert sprites
        handler = MonsterSpriteHandler(
            slug=monster.slug,
            sheet_path=loader.resolve_path(sprites.sheet),
            front_rect=sprites.front_rect,
            back_rect=sprites.back_rect,
            menu1_rect=sprites.menu1_rect,
            menu2_rect=sprites.menu2_rect,
        )
        if handler is None:
            return
        sprite = handler.get_sprite("front", scale=self.factor)
        new_image = self._create_image_from_surface(sprite.image)
        image_widget = menu.add.image(image_path=new_image.copy())
        image_widget.set_float(origin_position=True)
        image_widget.translate(fxw(53.6 / 256), fxh(10 / 144))

    def __init__(
        self,
        client: BaseClient,
        character: NPC,
        monster: MonsterModel | None,
        source: str,
        reveal: bool = False,
        **kwargs: Any,
    ) -> None:

        if not lookup_cache:
            _lookup_monsters()
        if monster is None:
            raise ValueError("No monster")

        self.char = character
        self.source = source
        self.is_visible = self.char.tuxepedia.is_caught(monster.slug) or reveal
        self._monster = monster
        width, height = client.context.resolution

        super().__init__(client=client, height=height, width=width, **kwargs)

        theme = self._setup_theme(BG_JOURNAL_INFO)
        theme.scrollarea_position = POSITION_EAST
        theme.widget_alignment = ALIGN_CENTER
        self._menu_config["theme"] = theme

        self.add_menu_items(self.menu, monster)
        self.reset_theme()

    def _safe_display(self, value: str) -> str:
        return value if self.is_visible else "-----"

    def process_event(self, event: PlayerInput) -> PlayerInput | None:
        client = self.client
        monsters = self.char.tuxepedia.get_monsters()
        models = list(lookup_cache.values())
        model_dict = {model.slug: model for model in models}
        monster_models = sorted(
            [model_dict[mov] for mov in monsters if mov in model_dict],
            key=lambda x: x.txmn_id,
        )

        # LEFT / RIGHT → cycle monsters (with repeat)
        if (
            event.button in (buttons.RIGHT, buttons.LEFT)
            and self.valid_press(event)
            and self.source in ("JournalInfoState", "JournalState")
        ):
            if not monster_models:
                return None

            current_monster_index = monster_models.index(self._monster)
            new_index = (
                (current_monster_index + 1) % len(monster_models)
                if event.button == buttons.RIGHT
                else (current_monster_index - 1) % len(monster_models)
            )

            client.replace_state(
                "JournalInfoState",
                character=self.char,
                monster=monster_models[new_index],
                source=self.name,
            )
            return None

        # A / B / BACK → close (pressed only)
        elif (
            event.button in (buttons.BACK, buttons.B, buttons.A)
            and event.pressed
        ):
            client.remove_state_by_name("JournalInfoState")
            return None

        return None
