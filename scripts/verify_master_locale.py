"""
Do some basic checks of the DB to make sure translated string have references
in the master JSON locale.  translated strings are defined by having a
"_trans" suffix.

This isn't considered to be a comprehensive check

This is a very basic check right now.  Files with missing locale strings
will be listed on the bottom.  Eventually will add what are missing....

Program output is suitable to use as JSON in the master locale.
"""
from __future__ import print_function

import glob
import json
import re
from os.path import dirname, join, normpath

RESOURCES_DIR = normpath(join(dirname(__file__), '../../../tuxemon/resources'))

# assume run from tests folder
DB_ROOT = join(RESOURCES_DIR, 'db')
DB_TABLES = ['item', 'technique', 'monster']  # tables to check for translation slugs
MAP_ROOT = join(RESOURCES_DIR, 'maps')
MASTER_FILENAME = 'en_US.json'
LOCALE_PATH = join(DB_ROOT, 'locale', MASTER_FILENAME)


def load_keys(filename):
    with open(filename) as _fp:
        return set(json.load(_fp).keys())


def iter_dialog_keys(file):
    c1 = re.compile('.*translated_dialog(_chain)? (.*)".*')
    c2 = re.compile('.*translated_dialog_choice (.*)".*')
    with open(file, 'r') as f:
        for line in f:
            match = c1.match(line)
            if match:
                yield match.group(2)
            else:
                match = c2.match(line)
                if match:
                    s = match.group(1).split(",")[0].split(":")
                    yield s[0]
                    yield s[1]


def test_dialog():
    master_keys = load_keys(LOCALE_PATH)
    master_keys.add("${{end}}")
    test_pass = True
    for f in glob.glob(join(MAP_ROOT, '*.tmx')):
        errors = [
            key
            for key in iter_dialog_keys(f)
            if key not in master_keys
        ]

        if errors:
            if test_pass:
                print("Dialog Errors:")
            test_pass = False
            errors.insert(0, f)
            errors.append("")
            print("\n\t".join(errors))

    return test_pass


def test_translation_slugs():
    master_keys = load_keys(LOCALE_PATH)
    test_pass = True
    for table in DB_TABLES:
        for record_file in glob.glob(join(DB_ROOT, table, '*.json')):
            with open(join(record_file)) as _fp:
                record = json.load(_fp)
            errors = [
                "{} - {}".format(key, value)
                for key, value in record.items()
                if key.endswith("_trans") and value not in master_keys
            ]

            if errors:
                if test_pass:
                    print("%s Errors:" % table.title())
                test_pass = False
                errors.insert(0, record_file)
                errors.append("")
                print("\n\t".join(errors))

    return test_pass


if __name__ == "__main__":
    test_dialog()
    test_translation_slugs()
