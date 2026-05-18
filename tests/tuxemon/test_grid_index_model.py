# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import pytest

from tuxemon.menu.grid_index_model import GridIndexModel


def make(count, columns, rectangular, orientation):
    return GridIndexModel(
        count=count,
        columns=columns,
        rectangular=rectangular,
        orientation=orientation,
    )


@pytest.mark.parametrize(
    "count,columns,orientation,expected",
    [
        pytest.param(
            4,
            2,
            "horizontal",
            [(0, 0), (0, 1), (1, 0), (1, 1)],
            id="4_items_2cols_horizontal",
        ),
        pytest.param(
            5,
            3,
            "horizontal",
            [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1)],
            id="5_items_3cols_horizontal",
        ),
        pytest.param(
            4,
            2,
            "vertical",
            [(0, 0), (1, 0), (0, 1), (1, 1)],
            id="4_items_2cols_vertical",
        ),
        pytest.param(
            5,
            3,
            "vertical",
            [(0, 0), (1, 0), (2, 0), (0, 1), (1, 1)],
            id="5_items_3cols_vertical",
        ),
    ],
)
def test_lr_to_rowcol_basic(count, columns, orientation, expected):
    model = make(count, columns, False, orientation)
    results = [model.lr_to_rowcol(i) for i in range(count)]
    assert results == expected


def test_lr_to_rowcol_one_column_vertical():
    model = make(5, 1, False, "vertical")
    assert [model.lr_to_rowcol(i) for i in range(5)] == [
        (0, 0),
        (1, 0),
        (2, 0),
        (3, 0),
        (4, 0),
    ]


def test_lr_to_rowcol_more_columns_than_items_vertical():
    model = make(3, 10, False, "vertical")
    assert [model.lr_to_rowcol(i) for i in range(3)] == [
        (0, 0),
        (0, 1),
        (0, 2),
    ]


def test_lr_to_rowcol_rectangular():
    model = make(7, 3, True, "horizontal")
    assert [model.lr_to_rowcol(i) for i in range(7)] == [
        (0, 0),
        (0, 1),
        (0, 2),
        (1, 0),
        (1, 1),
        (1, 2),
        (2, 0),
    ]


def test_lr_to_rowcol_rectangular_vertical():
    model = make(7, 3, True, "vertical")
    assert [model.lr_to_rowcol(i) for i in range(7)] == [
        (0, 0),
        (1, 0),
        (2, 0),
        (0, 1),
        (1, 1),
        (2, 1),
        (0, 2),
    ]


def test_lr_to_rowcol_zero_items():
    model = make(0, 3, False, "horizontal")
    assert model.layout.rows == 0
    assert model.count == 0


@pytest.mark.parametrize(
    "count,columns,rectangular,orientation",
    [
        pytest.param(1, 1, False, "horizontal", id="1x1_ragged_h"),
        pytest.param(3, 2, False, "horizontal", id="3x2_ragged_h"),
        pytest.param(7, 3, False, "horizontal", id="7x3_ragged_h"),
        pytest.param(2, 1, True, "horizontal", id="2x1_rect_h"),
        pytest.param(2, 1, True, "vertical", id="2x1_rect_v"),
        pytest.param(5, 3, True, "horizontal", id="5x3_rect_h"),
        pytest.param(5, 3, True, "vertical", id="5x3_rect_v"),
        pytest.param(10, 4, True, "horizontal", id="10x4_rect_h"),
        pytest.param(10, 4, True, "vertical", id="10x4_rect_v"),
    ],
)
def test_lr_tb_roundtrip(count, columns, rectangular, orientation):
    model = make(count, columns, rectangular, orientation)

    # LR → TB → LR
    for lr in range(count):
        tb = model.lr_to_tb(lr)
        lr2 = model.tb_to_lr(tb)
        assert lr2 == lr

    # TB → LR → TB
    max_tb = model.layout.rows * model.columns if rectangular else count
    for tb in range(max_tb):
        lr = model.tb_to_lr(tb)
        tb2 = model.lr_to_tb(lr)
        assert tb2 == tb % max_tb


@pytest.mark.parametrize(
    "count,columns,orientation,start,delta,expected",
    [
        pytest.param(5, 3, "horizontal", 0, +1, 1, id="lr_move_forward"),
        pytest.param(5, 3, "horizontal", 0, -1, 4, id="lr_wrap_backward"),
        pytest.param(5, 3, "horizontal", 4, +1, 0, id="lr_wrap_forward"),
    ],
)
def test_move_lr(count, columns, orientation, start, delta, expected):
    model = make(count, columns, False, orientation)
    assert model.move_lr(start, delta) == expected


@pytest.mark.parametrize(
    "count,columns,orientation,start,delta",
    [
        pytest.param(5, 3, "horizontal", 0, +1, id="tb_move_forward"),
        pytest.param(5, 3, "horizontal", 0, -1, id="tb_move_backward"),
        pytest.param(5, 3, "vertical", 2, +1, id="tb_vertical_forward"),
    ],
)
def test_move_tb_roundtrip(count, columns, orientation, start, delta):
    model = make(count, columns, False, orientation)
    new_index = model.move_tb(start, delta)
    assert 0 <= new_index < count


def test_move_rectangular_basic():
    model = make(6, 3, True, "horizontal")
    # Grid:
    # 0 1 2
    # 3 4 5
    assert model.move_rectangular(0, "lr", +1) == 1
    assert model.move_rectangular(2, "lr", +1) == 3  # wrap to next row
    assert model.move_rectangular(3, "tb", +1) == 0  # wrap vertically


def test_move_rectangular_vertical():
    model = make(6, 3, True, "vertical")
    assert model.move_rectangular(0, "tb", +1) == 1
    assert model.move_rectangular(1, "tb", +1) == 2
    assert model.move_rectangular(2, "tb", +1) == 3


def test_zero_items_movement():
    model = make(0, 3, False, "horizontal")
    assert model.move(0, "lr", +1) == 0
    assert model.move(0, "tb", -1) == 0


def test_one_item_movement():
    model = make(1, 3, False, "horizontal")
    assert model.move(0, "lr", +1) == 0
    assert model.move(0, "tb", -1) == 0
