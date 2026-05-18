# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from tuxemon.entity.path.path_view import PathView


def test_empty_pathview():
    pv = PathView([])
    assert len(pv) == 0
    assert not pv
    assert pv.next() is None
    assert pv.consume() is None


def test_next_and_consume():
    pv = PathView([(1, 1), (2, 2)])
    assert pv.next() == (2, 2)
    assert pv.consume() == (2, 2)
    assert pv.next() == (1, 1)


def test_push():
    pv = PathView([])
    pv.push((3, 3))
    assert pv.next() == (3, 3)
    assert len(pv) == 1


def test_extend_reversed():
    pv = PathView([(0, 0)])
    pv.extend_reversed([(1, 1), (2, 2)])
    assert list(pv) == [(0, 0), (2, 2), (1, 1)]
    assert pv.next() == (1, 1)


def test_iteration_and_len():
    pv = PathView([(1, 1), (2, 2)])
    assert list(pv) == [(1, 1), (2, 2)]
    assert len(pv) == 2


def test_repr():
    pv = PathView([(1, 1)])
    assert "PathView" in repr(pv)


def test_prepend_inserts_at_start():
    pv = PathView([(2, 2), (3, 3)])
    pv.prepend((1, 1))
    assert list(pv) == [(1, 1), (2, 2), (3, 3)]
    assert pv.next() == (3, 3)


def test_peek_various_offsets():
    pv = PathView([(1, 1), (2, 2), (3, 3)])
    assert pv.peek(0) == (3, 3)
    assert pv.peek(1) == (2, 2)
    assert pv.peek(2) == (1, 1)
    assert pv.peek(3) is None


def test_replace_tail_replaces_entire_path():
    pv = PathView([(1, 1), (2, 2)])
    pv.replace_tail([(9, 9), (8, 8)])
    assert list(pv) == [(9, 9), (8, 8)]
    assert pv.next() == (8, 8)


def test_splice_appends_reversed_sequence():
    pv = PathView([(0, 0), (1, 1)])
    pv.splice([(5, 5), (6, 6)])
    assert list(pv) == [(0, 0), (1, 1), (6, 6), (5, 5)]
    assert pv.next() == (5, 5)


def test_clear_removes_all_tiles():
    pv = PathView([(1, 1), (2, 2)])
    pv.clear()
    assert len(pv) == 0
    assert pv.next() is None


def test_consumed_tracks_popped_tiles():
    pv = PathView([(1, 1), (2, 2), (3, 3)])
    assert pv.consume() == (3, 3)
    assert pv.consume() == (2, 2)
    assert pv.consumed() == [(3, 3), (2, 2)]
    assert list(pv) == [(1, 1)]
