# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""
Module mainly used for the mod_manager.py
"""
import os
from typing import Any


def symlink_missing(target: str, *sources: Any) -> None:
    """
    'Walks' through the specified directories, and symlinks missing files
    Parameters:
        target: The directory where symlinks are created
        sources: The source directories
    """

    for source in sources:
        # Read the source directory
        for i in os.listdir(source):
            # Ignore symlinking meta.json
            if i != "meta.json":
                # Link the contents on a directory
                full_path = os.path.join(source, i)
                if os.path.isdir(full_path):
                    for a in os.listdir(full_path):
                        try:
                            os.mkdir(os.path.join(target, i))
                        except FileExistsError:
                            pass

                        while True:
                            try:
                                os.symlink(
                                    os.path.join(source, i, a),
                                    os.path.join(target, i, a),
                                )
                                break
                            except FileExistsError:
                                if os.path.islink(os.path.join(target, i, a)):
                                    os.unlink(os.path.join(target, i, a))
                                else:
                                    os.replace(
                                        os.path.join(target, i, a),
                                        os.path.join(target, i, a + ".old"),
                                    )

                # Symlink the individual files
                else:
                    # fmt: off
                    try:
                        os.symlink(
                            os.path.join(source, i), os.path.join(target, i),
                        )
                    except FileExistsError:
                        continue
