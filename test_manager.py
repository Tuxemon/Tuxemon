from tuxemon.mod_manager import Manager

from pprint import pprint

#ip_list = ["http://127.0.0.1:5000", "http://127.0.0.1:5001"]
ip_list = ["http://127.0.0.1:5000"]
man = Manager(ip_list)

print("-"*10)
pprint(man.list_packages())

man.update_all()

pprint(man.list_packages())

print("-"*10)
for i in man.list_packages():
    print(i)

print(man.get_package_repo("package-name"))

man.download_package("package-name", 0)
"""
for i in ip_list:
    print(i)
    man.download_package("package", 0, i)
"""
