# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import pytest

from tuxemon.menu.grid_layout import GridLayout


def roundtrip(layout, orientation):
    # LR → TB → LR
    for lr in range(layout.count):
        tb = layout.lr_to_tb(lr, orientation)
        lr2 = layout.tb_to_lr(tb, orientation)
        assert lr2 == lr

    # TB → LR → TB
    max_tb = (
        layout.rows * layout.columns if layout.rectangular else layout.count
    )
    for tb in range(max_tb):
        lr = layout.tb_to_lr(tb, orientation)
        tb2 = layout.lr_to_tb(lr, orientation)
        assert tb2 == tb % max_tb


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
def test_roundtrip(count, columns, rectangular, orientation):
    layout = GridLayout(count, columns, rectangular)
    roundtrip(layout, orientation)


def test_zero_columns_clamped():
    layout = GridLayout(5, 0, rectangular=False)
    assert layout.columns == 1

    for i in range(5):
        assert layout.lr_to_tb(i, "horizontal") == i
        assert layout.tb_to_lr(i, "horizontal") == i


def test_large_grid_roundtrip():
    layout = GridLayout(500, 17, rectangular=False)
    roundtrip(layout, "horizontal")


def test_gridlayout_basic_properties():
    layout = GridLayout(7, 3, rectangular=False)
    assert layout.count == 7
    assert layout.columns == 3
    assert layout.rows == 2
    assert layout.remainder == 1


def test_gridlayout_rectangular_properties():
    layout = GridLayout(7, 3, rectangular=True)
    assert layout.count == 7
    assert layout.columns == 3
    assert layout.rows == 3  # ceil(7/3)


def test_ragged_grid_horizontal_mapping():
    # 7 items, 3 columns → rows=2, remainder=1
    layout = GridLayout(7, 3, rectangular=False)

    # LR layout:
    # 0 1 2
    # 3 4 5
    # 6 _ _
    assert layout.lr_to_tb(0, "horizontal") == 0
    assert layout.lr_to_tb(3, "horizontal") == 1
    assert layout.lr_to_tb(6, "horizontal") == 2  # last row, first col


def test_ragged_grid_vertical_mapping():
    layout = GridLayout(7, 3, rectangular=False)

    # Vertical orientation flips row/col meaning
    assert layout.lr_to_tb(0, "vertical") == 0
    assert layout.lr_to_tb(1, "vertical") == 1
    assert layout.lr_to_tb(3, "vertical") == 3


def test_rectangular_horizontal_mapping():
    layout = GridLayout(7, 3, rectangular=True)

    # Full grid:
    # 0 1 2
    # 3 4 5
    # 6 7 8 (virtual)
    assert layout.lr_to_tb(6, "horizontal") == 2  # row2,col0 → tb2
    assert layout.tb_to_lr(7, "horizontal") == 5  # virtual cell maps back


def test_rectangular_vertical_mapping():
    layout = GridLayout(7, 3, rectangular=True)

    # Vertical orientation:
    # TB enumerates row-major
    assert layout.lr_to_tb(0, "vertical") == 0
    assert layout.lr_to_tb(3, "vertical") == 3
    assert layout.lr_to_tb(6, "vertical") == 6


def test_single_item():
    layout = GridLayout(1, 3, rectangular=False)
    assert layout.lr_to_tb(0, "horizontal") == 0
    assert layout.tb_to_lr(0, "horizontal") == 0


def test_one_column_ragged():
    layout = GridLayout(5, 1, rectangular=False)
    for i in range(5):
        assert layout.lr_to_tb(i, "horizontal") == i
        assert layout.tb_to_lr(i, "horizontal") == i


def test_many_columns_more_than_items():
    layout = GridLayout(3, 10, rectangular=False)
    # rows=0, remainder=3
    assert layout.rows == 0
    assert layout.remainder == 3
    # All items are in the first row
    for i in range(3):
        assert layout.lr_to_tb(i, "horizontal") == i


def test_rectangular_many_columns():
    layout = GridLayout(3, 10, rectangular=True)
    assert layout.rows == 1  # ceil(3/10)
    for i in range(3):
        assert layout.lr_to_tb(i, "horizontal") == i


def test_zero_items_rectangular():
    layout = GridLayout(0, 3, rectangular=True)
    assert layout.rows == 0


def test_zero_items_ragged():
    layout = GridLayout(0, 3, rectangular=False)
    assert layout.rows == 0
    assert layout.remainder == 0


def test_vertical_ragged_not_invertible():
    layout = GridLayout(5, 3, rectangular=False)
    # Just assert that it runs without error
    for lr in range(5):
        tb = layout.lr_to_tb(lr, "vertical")
        lr2 = layout.tb_to_lr(tb, "vertical")
        assert 0 <= lr2 < 5


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
    layout = GridLayout(count, columns, rectangular=False)
    results = [layout.lr_to_rowcol(i, orientation) for i in range(count)]
    assert results == expected


def test_lr_to_rowcol_one_column_horizontal():
    layout = GridLayout(5, 1, rectangular=False)
    # Horizontal row-major with 1 column → all col=0
    assert [layout.lr_to_rowcol(i, "horizontal") for i in range(5)] == [
        (0, 0),
        (1, 0),
        (2, 0),
        (3, 0),
        (4, 0),
    ]


def test_lr_to_rowcol_one_column_vertical():
    layout = GridLayout(5, 1, rectangular=False)
    # Vertical column-major with 1 column → still all col=0
    assert [layout.lr_to_rowcol(i, "vertical") for i in range(5)] == [
        (0, 0),
        (1, 0),
        (2, 0),
        (3, 0),
        (4, 0),
    ]


def test_lr_to_rowcol_more_columns_than_items_horizontal():
    layout = GridLayout(3, 10, rectangular=False)
    # rows=0, remainder=3 → all items in row 0
    assert [layout.lr_to_rowcol(i, "horizontal") for i in range(3)] == [
        (0, 0),
        (0, 1),
        (0, 2),
    ]


def test_lr_to_rowcol_more_columns_than_items_vertical():
    layout = GridLayout(3, 10, rectangular=False)
    # Vertical column-major: rows = 0, remainder = 3 → treat as 1 row
    # So all items are row=0, col=i
    assert [layout.lr_to_rowcol(i, "vertical") for i in range(3)] == [
        (0, 0),
        (0, 1),
        (0, 2),
    ]


def test_lr_to_rowcol_rectangular_grid():
    layout = GridLayout(7, 3, rectangular=True)
    # rows = ceil(7/3) = 3
    # Horizontal row-major
    assert [layout.lr_to_rowcol(i, "horizontal") for i in range(7)] == [
        (0, 0),
        (0, 1),
        (0, 2),
        (1, 0),
        (1, 1),
        (1, 2),
        (2, 0),
    ]


def test_lr_to_rowcol_rectangular_vertical():
    layout = GridLayout(7, 3, rectangular=True)
    # rows = 3 → vertical column-major
    assert [layout.lr_to_rowcol(i, "vertical") for i in range(7)] == [
        (0, 0),
        (1, 0),
        (2, 0),
        (0, 1),
        (1, 1),
        (2, 1),
        (0, 2),
    ]


def test_lr_to_rowcol_zero_items():
    layout = GridLayout(0, 3, rectangular=False)
    # Should not crash; no indices to test
    assert layout.rows == 0
    assert layout.remainder == 0
