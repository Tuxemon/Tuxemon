# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import logging
import subprocess


def get_git_hash() -> str:
    """Gets the current Git hash."""
    try:
        githash = (
            subprocess.check_output(["git", "describe", "--always"])
            .strip()
            .decode()
        )
        return f"Git Hash: {githash}"
    except subprocess.CalledProcessError:
        logging.warning("Git command failed. Git hash not available.")
        return "N/A"
    except FileNotFoundError:
        logging.warning("Git not found. Git hash not available.")
        return "N/A"
