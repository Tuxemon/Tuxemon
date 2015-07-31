from ctypes import cdll

class Rumble(object):
    def __init__(self):
        pass

    def rumble(self, target=0, period=25, magnitude=24576, length=2000, delay=0):
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

