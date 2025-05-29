# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from pathlib import Path

from PIL import Image

from tuxemon.fusion import Body, fuse, replace_color


class TestFusion(unittest.TestCase):
    def setUp(self):
        self.image = Image.new("RGBA", (10, 10), (255, 0, 0, 255))  # Red image
        self.image_path = "test_image.png"
        self.image.save(self.image_path)

        self.body = Body()
        self.body.name = "test_body"
        self.body.body_image = self.image
        self.body.face_image = self.image
        self.body.primary_colors = [(255, 0, 0)]  # Red
        self.body.secondary_colors = [(0, 0, 255)]  # Blue
        self.body.tertiary_colors = [(0, 255, 0)]  # Green

    def tearDown(self):
        image_path = Path(self.image_path)
        if image_path.exists():
            image_path.unlink()

    def test_replace_color(self):
        result_image = replace_color(self.image, (255, 0, 0), (0, 0, 255))
        data = list(result_image.getdata())
        for pixel in data:
            self.assertEqual(pixel, (0, 0, 255, 255))

    def test_body_load(self):
        json_data = self.body.to_json()
        new_body = Body()
        new_body.load(json_data, file=False)
        self.assertEqual(new_body.name, "test_body")
        self.assertEqual(new_body.primary_colors, [(255, 0, 0)])

    def test_fuse(self):
        self.body_image = Image.new(
            "RGBA", (20, 20), (255, 0, 0, 255)
        )  # Red image
        self.face_image = Image.new(
            "RGBA", (10, 10), (0, 0, 255, 255)
        )  # Blue image

        self.body = Body()
        self.body.body_image = self.body_image
        self.body.face_position = (10, 10)
        self.body.head_size = (10, 10)

        self.face = Body()
        self.face.face_image = self.face_image
        self.face.head_size = (10, 10)
        fused_image = fuse(self.body, self.face, save=False)

        self.assertEqual(fused_image.size, (20, 20))

        pixel = fused_image.getpixel((10, 10))
        self.assertEqual(pixel, (0, 0, 255, 255))
