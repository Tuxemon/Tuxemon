"""
Do some basic checks of the DB to make sure translated string
have references in the master locale.  translated strings are
defined by having a "_trans" suffix.

This isn't considered to be a comprehensive check

This is a very basic check right now.  Files with missing locale strings
will be listed on the bottom.  Eventually will add what are missing....

Program output is suitable to use as JSON in the master locale.
"""
from __future__ import print_function

import glob
import json
from os.path import join, normpath

# assume run from tests folder
db_root = normpath('../tuxemon/resources/db')
locale_folder = join(db_root, 'locale')
db_tables = ['item', 'technique', 'monster']  # tables to check for translation slugs
master_filename = 'en_US.json'


def load_keys(filename):
    with open(filename) as _fp:
        return set(json.load(_fp).keys())


def iter_trans_values(table):
    for record_file in glob.glob(join(db_root, table, '*.json')):
        with open(join(record_file)) as _fp:
            record = json.load(_fp)
        for key, value in record.items():
            if key.endswith("_trans"):
                yield value


master_keys = load_keys(join(locale_folder, master_filename))
errors = set()

for table in db_tables:
    values = set(iter_trans_values(table))
    errors.update(values.difference(master_keys))

if errors:
    print("These items are non-conforming:")
    for lc in sorted(errors):
        print('    "{}": "",'.format(lc))
else:
    print("It all checks out.")
