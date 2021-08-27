from tuxemon.mod_manager import Manager

from pprint import pprint

ip_list = ["http://127.0.0.1:5000", "http://127.0.0.1:5001"]

man = Manager(ip_list)

pprint(man.list_packages())

for i in ip_list:
    print(i)
    man.download_package("package", 0, i)
