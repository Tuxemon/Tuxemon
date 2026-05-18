# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import pytest
from PIL import Image

from tuxemon.fusion import (
    Body,
    calculate_face_position,
    fuse,
    get_color_mappings,
    paste_face_onto_body,
    replace_color,
    replace_multiple_colors,
    resize_face_image,
)


@pytest.fixture
def red_image():
    return Image.new("RGBA", (10, 10), (255, 0, 0, 255))


@pytest.fixture
def blue_image():
    return Image.new("RGBA", (10, 10), (0, 0, 255, 255))


@pytest.fixture
def sample_body(red_image):
    b = Body()
    b.name = "test"
    b.body_image = red_image
    b.face_image = red_image
    b.primary_colors = [(255, 0, 0)]
    b.secondary_colors = [(0, 0, 255)]
    b.tertiary_colors = [(0, 255, 0)]
    b.head_size = (10, 10)
    b.face_position = (5, 5)
    return b


@pytest.fixture
def sample_face(blue_image):
    f = Body()
    f.name = "face"
    f.face_image = blue_image
    f.primary_colors = [(255, 0, 0)]
    f.secondary_colors = [(0, 0, 255)]
    f.tertiary_colors = [(0, 255, 0)]
    f.head_size = (10, 10)
    return f


def test_get_face_size(sample_body):
    size = sample_body.get_face_size()
    assert size == (10, 10)


def test_to_json_and_load(tmp_path, sample_body):
    json_path = tmp_path / "body.json"
    sample_body.save(json_path)
    new_body = Body()
    new_body.load(str(json_path))
    assert new_body.name == sample_body.name
    assert new_body.primary_colors == sample_body.primary_colors


def test_get_state(sample_body):
    state = sample_body.get_state()
    assert isinstance(state, dict)
    assert state["name"] == "test"


def test_set_state(sample_body):
    sample_body.set_state({"name": "updated"})
    assert sample_body.name == "updated"


def test_replace_color(red_image):
    result = replace_color(red_image, (255, 0, 0), (0, 0, 255))
    width, height = result.size
    for x in range(width):
        for y in range(height):
            r, g, b, a = result.getpixel((x, y))
            assert (r, g, b) == (0, 0, 255)


def test_replace_multiple_colors(red_image):
    mappings = [((255, 0, 0), (0, 255, 0))]
    result = replace_multiple_colors(red_image, mappings)
    width, height = result.size
    for x in range(width):
        for y in range(height):
            r, g, b, a = result.getpixel((x, y))
            assert (r, g, b) == (0, 255, 0)


def test_get_color_mappings(sample_body, sample_face):
    mappings = get_color_mappings(sample_body, sample_face)
    assert len(mappings) == 3
    assert mappings[0] == (
        sample_body.primary_colors[0],
        sample_face.primary_colors[0],
    )


def test_resize_face_image(blue_image):
    resized = resize_face_image(blue_image, (20, 20), (10, 10))
    assert resized.size == (20, 20)


def test_calculate_face_position(sample_body, blue_image):
    pos = calculate_face_position(sample_body, blue_image)
    assert pos == (5 - 5, 5 - 5)


def test_paste_face_onto_body(red_image, blue_image):
    result = paste_face_onto_body(red_image, blue_image, (0, 0))
    assert result.getpixel((0, 0)) == (0, 0, 255, 255)


def test_fuse(tmp_path, sample_body, sample_face):
    sample_body.body_image = Image.new("RGBA", (20, 20), (255, 0, 0, 255))
    sample_face.face_image = Image.new("RGBA", (10, 10), (0, 0, 255, 255))
    output = fuse(sample_body, sample_face, save=False)
    assert output.size == (20, 20)
    assert output.getpixel((5, 5)) == (0, 0, 255, 255)
