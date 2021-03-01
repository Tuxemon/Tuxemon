try:
    from ctypes import cdll
except:
    cdll = None

class Rumble:
    def __init__(self):
        pass

    def rumble(self, target=0, period=25, magnitude=24576, length=2, delay=0,
            attack_length=256, attack_level=0, fade_length=256, fade_level=0,
            direction=16384):
        pass

def find_library(locations):
    for path in locations:
        try:
            lib = cdll.LoadLibrary(path)
            library = path
        except OSError as e:
            lib_shake = None
            library = None
        if library:
            return library

    return None

