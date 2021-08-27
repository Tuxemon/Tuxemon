from tuxemon.mod_manager import Manager

from pprint import pprint

man = Manager()

pprint(man.list_packages())

man.download_package("package", 0, "http://127.0.0.1:5000")
