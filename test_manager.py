from tuxemon.mod_manager import Manager

from pprint import pprint

man = Manager()

pprint(man.list_packages())

man.download_package("marcin", "tuxemon-main", 0)
