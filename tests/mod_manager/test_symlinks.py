import unittest


class TestSymlinks(unittest.TestCase):
    def test_linking(self):
        from tuxemon.symlink_missing import symlink_missing
        path = "/home/vxtreniusx/Tuxemon/"
        breakpoint()
        symlink_missing(path + "mods/1", path + "mods/2")

if __name__ == '__main__':
    unittest.main()
