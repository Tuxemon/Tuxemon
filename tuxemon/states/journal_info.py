# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

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
from tuxemon.platform.const.graphics import BG_JOURNAL_INFO, SEA_BLUE_COLOR
from tuxemon.platform.const.sizes import U_CM, U_FT, U_KG, U_LB, U_M, U_T
from tuxemon.tools import transform_resource_filename

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.entity.npc import NPC
    from tuxemon.platform.events import PlayerInput


class JournalInfoState(PygameMenuState):
    """Shows journal (screen 3/3)."""

    name: ClassVar[str] = "JournalInfoState"

    def add_menu_items(self, menu: Menu, monster: MonsterModel) -> None:


        minimal_font = transform_resource_filename(
            "font", self.client.config.locale.minimal_font_file
        )

        thin_font = transform_resource_filename(
            "font", self.client.config.locale.thin_font_file
        )


        orig_w = menu._width
        orig_h = menu._height

        def fxw(nominal_px: float) -> int:
            return round(orig_w * nominal_px / 256)

        def fxh(nominal_px: float) -> int:
            return round(orig_h * nominal_px / 144)

        # evolutions
        evo = T.translate("no_evolution")
        if monster.evolutions:
            evo = T.translate(
                "yes_evolution"
                if len(monster.evolutions) == 1
                else "yes_evolutions"
            )

        # weight and height
        unit = self.client.config.unit_measure
        if unit == "metric":
            if monster.weight >= 1000:
                mon_weight = f"{monster.weight / 1000:.1f}"
                unit_weight = U_T
            else:
                mon_weight = round(monster.weight)
                unit_weight = U_KG
            if monster.height >= 100:
                mon_height = f"{monster.height / 100:.1f}"
                unit_height = U_M
            else:
                mon_height = round(monster.height)
                unit_height = U_CM
        else:
            mon_weight = formula.convert_lbs(monster.weight)
            mon_height = formula.convert_ft(monster.height)
            unit_weight = U_LB
            unit_height = U_FT
        # name
        menu._auto_centering = False
        name = T.translate(monster.slug)
        lab1: Any = menu.add.label(
            title=name,
            label_id="name",
            font_size=self.font_type.biggest,
            align=ALIGN_LEFT,
            float=True,
            float_origin_position=True,
            padding=0,
            underline=True,
            underline_color=SEA_BLUE_COLOR,
            underline_offset=self.client.context.scaling.scale_int(1),
            underline_width=self.client.context.scaling.scale_int(1),
        )
        lab1.translate(fxw(119), fxh(8))

        # weight
        _weight = f"{T.translate('weight')}: {mon_weight} {unit_weight}"
        lab2: Any = menu.add.label(
            title=_weight,
            label_id="weight",
            font_size=self.font_type.biggest,
            font_name=minimal_font,
            align=ALIGN_LEFT,
            float=True,
            float_origin_position=True,
            padding=0,
        )
        lab2.translate(fxw(119), fxh(32))
        # height
        _height = f"{T.translate('height')}: {mon_height} {unit_height}"
        lab3: Any = menu.add.label(
            title=_height,
            label_id="height",
            font_size=self.font_type.biggest,
            font_name=minimal_font,
            align=ALIGN_LEFT,
            float=True,
            float_origin_position=True,
            padding=0,
        )
        lab3.translate(fxw(119), fxh(39))
        # type
        if self.is_visible:
            path1 = f"gfx/ui/icons/element/{monster.types[0]}_type_small.png"
            type_image_1 = self._create_image(path1)
            type_image_1.scale(self.factor, self.factor)
            if len(monster.types) > 1:
                path2 = f"gfx/ui/icons/element/{monster.types[1]}_type_small.png"
                type_image_2 = self._create_image(path2)
                type_image_2.scale(self.factor, self.factor)
                menu.add.image(
                    type_image_1, float=True,
                    float_origin_position=True, padding=0,
                ).translate(fxw(119), fxh(45))
                menu.add.image(
                    type_image_2, float=True,
                    float_origin_position=True, padding=0,
                ).translate(fxw(150), fxh(53))
            else:
                menu.add.image(
                    type_image_1, float=True,
                    float_origin_position=True, padding=0,
                ).translate(fxw(119), fxh(48))

        menu_type_suffix = T.translate("monster_menu_type_suffix")

        if len(monster.types) > 1:

            # FIRST TYPE
            type1_text = self._safe_display(monster.types[0])

            lab5a = menu.add.label(
                title=f"{type1_text}{menu_type_suffix}",
                label_id="type_loaded_1",
                font_size=self.font_type.biggest,
                font_name=minimal_font,
                align=ALIGN_LEFT,
                float=True,
                float_origin_position=True,
                padding=0,
            )

            lab5a.translate(fxw(132), fxh(48))

            type2_text = self._safe_display(monster.types[1])

            lab5b = menu.add.label(
                title=f"{type2_text}{menu_type_suffix}",
                label_id="type_loaded_2",
                font_size=self.font_type.biggest,
                font_name=minimal_font,
                align=ALIGN_LEFT,
                float=True,
                float_origin_position=True,
                padding=0,
            )

            lab5b.translate(fxw(164), fxh(57))

        else:
                # FIRST TYPE
                type1_text = self._safe_display(monster.types[0])

                lab5a = menu.add.label(
                    title=f"{type1_text}{menu_type_suffix}",
                    label_id="type_loaded_1",
                    font_size=self.font_type.biggest,
                    font_name=minimal_font,
                    align=ALIGN_LEFT,
                    float=True,
                    float_origin_position=True,
                    padding=0,
                )

                lab5a.translate(fxw(132), fxh(51))



        # shape
        menu_shape = T.translate("monster_menu_shape_short")
        _shape = T.translate(monster.shape)
        shape = f"{_shape} {menu_shape}"
        lab6: Any = menu.add.label(
            title=shape,
            label_id="shape",
            font_size=self.font_type.biggest,
            align=ALIGN_LEFT,
            font_name=thin_font,
            float=True,
            float_origin_position=True,
            padding=0,
        )
        lab6.translate(fxw(119), fxh(66))
        # species
        spec = T.translate(f"cat_{monster.species}")
        spec = self._safe_display(spec)
        species = spec + " " + T.translate("monster_menu_species")
        lab7: Any = menu.add.label(
            title=species,
            label_id="species",
            font_size=self.font_type.biggest,
            align=ALIGN_LEFT,
            font_name=thin_font,
            float=True,
            float_origin_position=True,
            padding=0,
        )
        lab7.translate(fxw(119), fxh(21))
        # txmn_id
        _txmn_id = f"{monster.txmn_id:03d}"
        lab8: Any = menu.add.label(
            title=_txmn_id,
            label_id="txmn_id",
            font_size=self.font_type.biggest,
            font_name=minimal_font,
            align=ALIGN_LEFT,
            float=True,
            float_origin_position=True,
            padding=0,
        )
        lab8.translate(fxw(14), fxh(68))

        # description
        desc = T.translate(f"{monster.slug}_description")
        desc = self._safe_display(desc)
        desc_frame = menu.add.frame_v(
            fxw(255),
            fxh(57),
            float=True,
            float_origin_position=True,
            frame_id="description_frame",
            padding=0,
        )
        desc_frame._relax=True
        desc_frame.translate(fxw(8), fxh(85))
        lab9: Any = menu.add.label(
            title=desc,
            label_id="description",
            font_size=self.font_type.biggest,
            wordwrap=True,
            leading=50,
            align=ALIGN_LEFT,
            float=True,
            float_origin_position=True,
            padding=0,
        )

        lab9.translate(fxw(8), fxh(85))

        # evolution monsters
        slugs = [ele.monster_slug for ele in monster.evolutions]
        elements = list(dict.fromkeys(slugs))

        evolution_names = ", ".join(
            T.translate(ele) for ele in elements
        )

        evolution_text = f"{evo}: {evolution_names}"

        lab10: Any = menu.add.label(
            title=self._safe_display(evolution_text),
            label_id="evolution",
            font_size=self.font_type.biggest,
            wordwrap=True,
            align=ALIGN_LEFT,
            float=True,
            float_origin_position=True,
            padding=0,
        )

        lab10.translate(fxw(22), fxh(128))

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
        image_widget.translate(fxw(45), fxh(6))

    def __init__(
        self,
        client: BaseClient,
        character: NPC,
        monster: MonsterModel | None,
        source: str,
        reveal: bool = False,
        **kwargs: Any,
    ) -> None:
        MonsterModel.load_cache(db)
        self.cache = MonsterModel.get_cache()

        if monster is None:
            raise ValueError("No monster")

        self.char = character
        self.source = source
        self.is_visible = self.char.tuxepedia.is_caught(monster.slug) or reveal
        self._monster = monster
        width, height = client.context.resolution

        super().__init__(client=client, height=height, width=width, **kwargs)

        theme = self._setup_theme(BG_JOURNAL_INFO)
        theme.widget_font_shadow = False
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
        models = list(self.cache.values())
        model_dict = {model.slug: model for model in models}
        monster_models = sorted(
            [model_dict[mov] for mov in monsters if mov in model_dict],
            key=lambda x: x.txmn_id,
        )

        # LEFT / RIGHT / DOWN → cycle monsters (with repeat)
        if (
            event.button in (buttons.RIGHT, buttons.LEFT, buttons.DOWN, buttons.UP)
            and self.valid_press(event)
            and self.source in ("JournalInfoState", "JournalState")
        ):
            if not monster_models:
                return None

            current_monster_index = monster_models.index(self._monster)
            new_index = (
                (current_monster_index + 1) % len(monster_models)
                if event.button in (buttons.RIGHT, buttons.DOWN)
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
