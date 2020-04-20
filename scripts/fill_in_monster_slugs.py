"""
Tool for quickly filling in slugs into monster json data files.

This tool may or may not have much use beyond brute force fixing
of some translation issues.

The script will read a tuxemon json file, read the slug, then
fill in sane defaults for the name, description, and category.

If values are already existing, then it will not overwrite them.

For most, if not all, situations, this will be the best format
for the current slug/translation system as of 2016-07-17.

This is not json aware, so the order of the file elements will
not change.  Attempting to rewrite this using a json lib will
likely reorder the files and make them less tidy.

- Leif
"""
from __future__ import print_function

import glob
import re
from os.path import normpath, join

# assume run from tests folder
db_root = normpath('../tuxemon/resources/db')
db_tables = ['monster']  # tables to check for translation slugs
master_filename = 'en_US.json'

# replacement regex table
# the regular expression table is need so that
# the json doesn't need to be in any order.
# 1: json name, 2: suffix added to slug
regex_table = dict()
sub_table = dict()
suffix_table = {
    'slug': '',
    'name_trans': '_name',
    'description_trans': '_descr',
    'category_trans': '_category'
}

# build table of regex for searching
for name, suffix in suffix_table.items():
    pattern = '(?P<ident>\s*)"(?P<key>{0})":(?P<space>\s+)"(?P<value>.*)"'.format(name)
    regex_table[name] = re.compile(pattern)

for table in db_tables:
    for fn in glob.glob(join(db_root, table, "*.json")):
        with open(fn) as fp:
            data = fp.read()

        # first extract data from the file
        # this will apply the regular expressions and make a dict with data
        working_dict = dict()
        for name, regex in regex_table.items():
            match = regex.search(data)
            if match:
                d = {'match': match.group(0)}
                d.update(match.groupdict())
                working_dict[name] = d

        # second, make replacements in the file with new values
        # unlike using a json lib, this will not rearrange the file contents
        changed = False
        for name, suffix in suffix_table.items():
            if suffix:
                repl = working_dict['slug']['value'] + suffix
                old = working_dict[name]['match']
                # the next couple lines can be used to get json to copy/paste to master locale
                value = working_dict[name]['value']
                print('    "{}": "{}",'.format(repl, value))
                # new = old.replace('""', '"{}"'.format(repl))
                # data = data.replace(old, new)
                # changed = True

        # if anything has changed, then save the file with changes
        if changed:
            with open(fn, "w") as fp:
                fp.write(data)
