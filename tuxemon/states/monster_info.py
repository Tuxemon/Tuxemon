# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from pygame_menu.locals import ALIGN_CENTER, ALIGN_LEFT, POSITION_EAST
from pygame_menu.menu import Menu

from tuxemon import formula
from tuxemon.database.runtime import db
from tuxemon.db import MonsterModel, TasteModel
from tuxemon.locale.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.menu.theme import get_theme
from tuxemon.monster.monster import Monster
from tuxemon.monster.renderer import MonsterRenderer
from tuxemon.platform.const import buttons
from tuxemon.platform.const.graphics import INDIV_INFO
from tuxemon.platform.const.sizes import U_CM, U_FT, U_KG, U_LB, U_M, U_T
from tuxemon.tools import fix_measure, transform_resource_filename

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.platform.events import PlayerInput


class MonsterInfoState(PygameMenuState):
    """
    Shows details of the single monster with the journal
    background graphic.
    """

    name: ClassVar[str] = "MonsterInfoState"

    def add_menu_items(
        self,
        menu: Menu,
        monster: Monster,
    ) -> None:

        def fxw(r: float) -> int:
            return fix_measure(menu._width, r)

        def fxh(r: float) -> int:
            return fix_measure(menu._height, r)

        menu._width = fxw(1)

        background = self._create_image(INDIV_INFO)
        background.scale(self.factor, self.factor)
        background_widget = menu.add.image(image_path=background)
        background_widget.set_float(origin_position=True)
        background_widget.translate(fxw(0 / 256), fxh(0 / 144))

        # weight and height
        models = list(self.monster_cache.values())
        results = next(
            (model for model in models if model.slug == monster.slug), None
        )
        if results is None:
            return

        unit = self.client.config.unit_measure
        if unit == "metric":
            if monster.weight >= 1000:
                mon_weight = f"{monster.weight / 1000:.1f}{U_T}"
            else:
                mon_weight = f"{round(monster.weight)}{U_KG}"
            if monster.height >= 100:
                mon_height = f"{monster.height / 100:.1f}{U_M}"
            else:
                mon_height = f"{round(monster.height)}{U_CM}"
        else:
            mon_weight = f"{formula.convert_lbs(monster.weight)}{U_LB}"
            mon_height = f"{formula.convert_ft(monster.height)}{U_FT}"
        # name
        menu._auto_centering = False
        thin_font_path = transform_resource_filename(
            "font", self.client.config.locale.thin_font_file
        )
        dark_color = (0x5D, 0x41, 0x07)
        light_color = (0x8A, 0x6F, 0x30)
        lab1: Any = menu.add.label(
            title=f"{monster.name.upper()}",
            label_id="name",
            font_size=self.font_type.biggest,
            align=ALIGN_LEFT,
            float=True,
            font_color=dark_color,
        )
        lab1.translate(fxw(37 / 256), fxh(9.8 / 144))
        # level + exp
        lab2: Any = menu.add.label(
            title=f"Lv. {monster.level}",
            label_id="level",
            font_size=self.font_type.biggest,
            align=ALIGN_LEFT,
            float=True,
            font_color=dark_color,
        )
        lab2.translate(fxw(169 / 256), fxh(12.8 / 144))

        # how much XP earned since last level-up
        x = monster.experience_handler.experience_current_level

        # how much XP is needed in total to level up
        y = monster.experience_handler.experience_for_next_level

        lab3: Any = menu.add.label(
            title=f"{x:,}/",  # add commas for readability
            label_id="exp",
            font_size=self.font_type.biggest,
            align=ALIGN_LEFT,
            float=True,
            font_color=dark_color,
        )
        lab3.translate(fxw(84 / 256), fxh(86.8 / 144))

        lab3b: Any = menu.add.label(
            title=f"{y:,}",  # add commas for readability
            label_id="exp2",
            font_size=self.font_type.biggest,
            align=ALIGN_LEFT,
            float=True,
            font_color=dark_color,
        )
        lab3b.translate(fxw(92 / 256), fxh(96.8 / 144))

        # section labels
        height_label: Any = menu.add.label(
            title=T.translate("height"),
            label_id="label-height",
            font_size=self.font_type.biggest,
            align=ALIGN_LEFT,
            float=True,
            font_name=thin_font_path,
            font_color=light_color,
        )
        height_label.translate(fxw(79 / 256), fxh(25.8 / 144))

        weight_label: Any = menu.add.label(
            title=T.translate("weight"),
            label_id="label-weight",
            font_size=self.font_type.biggest,
            align=ALIGN_LEFT,
            float=True,
            font_name=thin_font_path,
            font_color=light_color,
        )
        weight_label.translate(fxw(118 / 256), fxh(25.8 / 144))

        tastes_label: Any = menu.add.label(
            title=T.translate("tastes"),
            label_id="label-tastes",
            font_size=self.font_type.biggest,
            align=ALIGN_LEFT,
            float=True,
            font_name=thin_font_path,
            font_color=light_color,
        )
        tastes_label.translate(fxw(79 / 256), fxh(48.8 / 144))

        exp_label: Any = menu.add.label(
            title=T.translate("exp_to_next_level"),
            label_id="label-exp-next",
            font_size=self.font_type.biggest,
            align=ALIGN_LEFT,
            float=True,
            font_name=thin_font_path,
            font_color=light_color,
        )
        exp_label.translate(fxw(79 / 256), fxh(78.8 / 144))

        if monster.gender_symbol:
            lab_gender: Any = menu.add.label(
                title=monster.gender_symbol,
                label_id="gender",
                font_size=self.font_type.biggest,
                align=ALIGN_LEFT,
                font_color=dark_color,
                float=True,
            )
            lab_gender.translate(fxw(11 / 256), fxh(9 / 144))

        # weight
        lab4: Any = menu.add.label(
            title=mon_weight,
            label_id="weight",
            font_size=self.font_type.biggest,
            align=ALIGN_LEFT,
            float=True,
            font_color=dark_color,
        )
        lab4.translate(fxw(122 / 256), fxh(34.8 / 144))
        # height
        lab5: Any = menu.add.label(
            title=mon_height,
            label_id="height",
            font_size=self.font_type.biggest,
            align=ALIGN_LEFT,
            float=True,
            font_color=dark_color,
        )
        lab5.translate(fxw(84 / 256), fxh(34.8 / 144))

        # taste
        cold = T.translate(f"taste_{monster.taste_cold.lower()}")
        warm = T.translate(f"taste_{monster.taste_warm.lower()}")
        lab8: Any = menu.add.label(
            title=f"{warm}",
            label_id="taste-warm",
            font_size=self.font_type.biggest,
            align=ALIGN_LEFT,
            float=True,
            font_color=dark_color,
        )
        lab8.translate(fxw(84 / 256), fxh(58 / 144))

        lab9: Any = menu.add.label(
            title=f"{cold}",
            label_id="taste-cold",
            font_size=self.font_type.biggest,
            align=ALIGN_LEFT,
            float=True,
            font_color=dark_color,
        )
        lab9.translate(fxw(84 / 256), fxh(66 / 144))

        # capture
        lab10: Any = menu.add.label(
            title=monster.acquisition_string,
            label_id="capture",
            font_size=self.font_type.biggest,
            align=ALIGN_LEFT,
            float=True,
            font_name=thin_font_path,
            font_color=dark_color,
        )
        lab10.translate(fxw(38 / 256), fxh(118.8 / 144))

        # type icons (first and second type separately)
        types = monster.types.current

        if len(types) >= 1:
            type1_icon = self._create_image(
                f"gfx/ui/icons/element/{types[0].slug}_type_watermark.png"
            )
            type1_icon.scale(self.factor, self.factor)
            icon1_widget = menu.add.image(image_path=type1_icon)
            icon1_widget.set_float(origin_position=True)
            # Position of type 1 (set wherever you want)
            icon1_widget.translate(fxw(148 / 256), fxh(61 / 144))

        if len(types) >= 2:
            type2_icon = self._create_image(
                f"gfx/ui/icons/element/{types[1].slug}_type_watermark.png"
            )
            type2_icon.scale(self.factor, self.factor)
            icon2_widget = menu.add.image(image_path=type2_icon)
            icon2_widget.set_float(origin_position=True)
            # Position of type 2 (independent from type 1)
            icon2_widget.translate(fxw(131 / 256), fxh(45 / 144))

        # hp
        lab11: Any = menu.add.label(
            title=f"{monster.hp}",
            label_id="hp",
            font_size=self.font_type.biggest,
            align=ALIGN_LEFT,
            float=True,
            font_color=dark_color,
        )
        lab11.translate(fxw(200 / 256), fxh(34.8 / 144))
        # armour
        lab12: Any = menu.add.label(
            title=f"{monster.armour}",
            label_id="armour",
            font_size=self.font_type.biggest,
            align=ALIGN_LEFT,
            float=True,
            font_color=dark_color,
        )
        lab12.translate(fxw(200 / 256), fxh(47.8 / 144))
        # dodge
        lab13: Any = menu.add.label(
            title=f"{monster.dodge}",
            label_id="dodge",
            font_size=self.font_type.biggest,
            align=ALIGN_LEFT,
            float=True,
            font_color=dark_color,
        )
        lab13.translate(fxw(200 / 256), fxh(60.8 / 144))
        # melee
        lab14: Any = menu.add.label(
            title=f"{monster.melee}",
            label_id="melee",
            font_size=self.font_type.biggest,
            align=ALIGN_LEFT,
            float=True,
            font_color=dark_color,
        )
        lab14.translate(fxw(200 / 256), fxh(72.8 / 144))
        # ranged
        lab15: Any = menu.add.label(
            title=f"{monster.ranged}",
            label_id="ranged",
            font_size=self.font_type.biggest,
            align=ALIGN_LEFT,
            float=True,
            font_color=dark_color,
        )
        lab15.translate(fxw(200 / 256), fxh(85.8 / 144))
        # speed
        lab16: Any = menu.add.label(
            title=f"{monster.speed}",
            label_id="speed",
            font_size=self.font_type.biggest,
            align=ALIGN_LEFT,
            float=True,
            font_color=dark_color,
        )
        lab16.translate(fxw(200 / 256), fxh(98.8 / 144))

        stat_positions = {
            "hp": (fxw(165 / 256), fxh(34.8 / 144)),
            "armour": (fxw(165 / 256), fxh(47.8 / 144)),
            "dodge": (fxw(165 / 256), fxh(60.8 / 144)),
            "melee": (fxw(165 / 256), fxh(72.8 / 144)),
            "ranged": (fxw(165 / 256), fxh(85.8 / 144)),
            "speed": (fxw(165 / 256), fxh(98.8 / 144)),
        }

        stat_labels = {
            "hp": T.translate("short_hp"),
            "armour": T.translate("armour"),
            "dodge": T.translate("dodge"),
            "melee": T.translate("melee"),
            "ranged": T.translate("ranged"),
            "speed": T.translate("speed"),
        }

        for stat, title in stat_labels.items():
            stat_label: Any = menu.add.label(
                title=title,
                label_id=f"label-{stat}",
                font_size=self.font_type.biggest,
                align=ALIGN_LEFT,
                float=True,
                font_name=thin_font_path,
                font_color=light_color,
            )
            x, y = stat_positions[stat]
            stat_label.translate(x, y)

        plus_icon = self._create_image("gfx/ui/icons/plusminus/plus.png")
        minus_icon = self._create_image("gfx/ui/icons/plusminus/minus.png")
        plus_icon.scale(self.factor, self.factor)
        minus_icon.scale(self.factor, self.factor)

        # Helper: find which stat a taste affects
        def get_stat_for_taste(slug: str) -> str | None:
            taste = self.taste_cache.get(slug.lower())
            if not taste or not taste.modifiers:
                return None

            for modifier in taste.modifiers:
                if modifier.attribute == "stat" and modifier.values:
                    return modifier.values[0]

            return None

        # Warm taste gives +10%
        warm_stat = get_stat_for_taste(monster.taste_warm)
        if warm_stat in stat_positions:
            x, y = stat_positions[warm_stat]
            plus = menu.add.image(image_path=plus_icon.copy())
            plus.set_float(origin_position=True)
            plus.translate(x + fxw(36 / 256), y + (0.2 / 144))

        # Cold taste gives -10%
        cold_stat = get_stat_for_taste(monster.taste_cold)
        if cold_stat in stat_positions:
            x, y = stat_positions[cold_stat]
            minus = menu.add.image(image_path=minus_icon.copy())
            minus.set_float(origin_position=True)
            minus.translate(x + fxw(36 / 256), y + (0.2 / 144))

        # bond icon
        owner = self.client.get_monster_owner(monster)
        if owner and owner.bag.find_item("friendship_scroll"):
            bond_file = monster.bond_handler.get_bond_icon_path()
            if bond_file:
                bond_icon = self._create_image(bond_file)
                bond_icon.scale(self.factor, self.factor)
                bond_widget = menu.add.image(image_path=bond_icon)
                bond_widget.set_float(origin_position=True)
                bond_widget.translate(fxw(20 / 256), fxh(29 / 144))

        # image
        renderer = MonsterRenderer(monster, scale=self.factor)
        surface = renderer.get_sprite("front").image
        new_image = self._create_image_from_surface(surface)
        image_widget = menu.add.image(image_path=new_image.copy())
        image_widget.set_float(origin_position=True)
        image_widget.translate(fxw(16 / 256), fxh(27 / 144))
        # tuxeball
        tuxeball = self._create_image(
            f"gfx/items/{monster.capture_device}.png"
        )
        tuxeball.scale(self.factor, self.factor)
        capture_device = menu.add.image(image_path=tuxeball)
        capture_device.set_float(origin_position=True)
        capture_device.translate(fxw(17 / 256), fxh(110 / 144))

    def __init__(
        self,
        client: BaseClient,
        monster: Monster,
        source: str,
        monsters: list[Monster] | None,
        **kwargs: Any,
    ) -> None:
        MonsterModel.load_cache(db)
        self.monster_cache = MonsterModel.get_cache()
        TasteModel.load_cache(db)
        self.taste_cache = TasteModel.get_cache()

        width, height = client.context.resolution

        self._monster = monster
        self._source = source
        self._monsters = monsters

        super().__init__(client=client, height=height, width=width, **kwargs)

        theme = get_theme(self.client.context.scaling).copy()
        theme.scrollarea_position = POSITION_EAST
        theme.widget_alignment = ALIGN_CENTER
        theme.widget_font_shadow = False
        theme.widget_padding = (0, 0)
        self._menu_config["theme"] = theme

        self.add_menu_items(self.menu, monster)
        self.reset_theme()

    def process_event(self, event: PlayerInput) -> PlayerInput | None:
        param: dict[str, Any] = {"source": self._source}
        client = self.client

        if self._source in [
            "WorldMenuState",
            "MonsterMenuState",
            "MonsterTakeState",
        ]:
            monsters = self._monsters
            if not monsters:
                return None

            param["monsters"] = monsters

            slot = monsters.index(self._monster)

            if event.button == buttons.RIGHT and self.valid_press(event):
                slot = (slot + 1) % len(monsters)
                param["monster"] = monsters[slot]
                client.replace_state("MonsterInfoState", **param)
            elif event.button == buttons.LEFT and self.valid_press(event):
                slot = (slot - 1) % len(monsters)
                param["monster"] = monsters[slot]
                client.replace_state("MonsterInfoState", **param)

        if (
            event.button in (buttons.BACK, buttons.B, buttons.A)
            and event.pressed
        ):
            client.remove_state_by_name("MonsterInfoState")

        return None
