"""
Check to see if locales differ from the master locale

The master locale is the US English locale.


This will check all locales and print locales that do not conform.

Output is JSON, suitable to copy/paste into a locale file.
"""
from __future__ import print_function

import glob
import json
import os

# assume run from test folder
locale_folder = '../tuxemon/resources/db/locale/'
locale_glob = locale_folder + '*.json'
master_filename = 'en_US.json'


def load_keys(filename):
    with open(filename) as _fp:
        return set(json.load(_fp).keys())


def print_list(sequence):
    for i in sorted(sequence):
        print("\t", i)


def print_json(sequence):
    for i in sorted(sequence):
        print('    "{}": "",'.format(i))


master_keys = load_keys(locale_folder + master_filename)
errors = set()

for lc in glob.glob(locale_glob):
    keys = load_keys(lc)

    # this will check the master locale against the master_set
    # it could take some effort to skip it, mangling paths
    # so i'm not going to bother for now
    if keys == master_keys:
        print(lc, ": ok")

    else:
        errors.add(os.path.basename(lc))
        missing = master_keys.difference(keys)
        if missing:
            print(lc, " The following are missing:")
            print_json(missing)
            print()

        extra = keys.difference(master_keys)
        if extra:
            print(lc, " The following are not define in master:")
            print_json(extra)
            print()

if errors:
    print("These locales are non-conforming:")
    print_list(errors)
else:
    print("It all checks out.")
