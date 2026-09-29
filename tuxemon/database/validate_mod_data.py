# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from tuxemon.database.bootstrap import bootstrap_database


def validate_mod_data() -> None:
    db = bootstrap_database()
    db.preload()
    db.load()

    errors = []
    tables_by_mod = db._config.mod_tables

    for mod, tables in tables_by_mod.items():
        if mod not in db._config.active_mods:
            continue

        print(f"Checking mod: {mod}")

        for table in tables:
            print(f"  Checking table: {table}")

            if table not in db._query_manager.all_data:
                errors.append(f"Missing table: {table}")
                continue

            entries = db._query_manager.all_data[table]

            if not entries:
                errors.append(f"Table '{table}' is empty")
                continue

    if errors:
        raise SystemExit("Database validation failed:\n" + "\n".join(errors))

    print("SUCCESS: All tables validated.")
