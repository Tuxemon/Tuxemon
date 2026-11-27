# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import os
import sys
from pathlib import Path

import pygame
import pytest
from _pytest.mark.structures import ParameterSet

# Tests run headless by default: the fixture below calls
# pygame.display.set_mode() for every test module, and on a desktop
# each call opens a real window that takes keyboard focus.
# To get the windows back, run with TUXEMON_TEST_WINDOWS=1, or set
# SDL_VIDEODRIVER yourself.
if os.environ.get("TUXEMON_TEST_WINDOWS", "") in ("", "0"):
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")


@pytest.fixture(scope="module", autouse=True)
def pygame_init():
    pygame.init()
    pygame.display.set_mode((800, 600))
    yield
    pygame.quit()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Enhance test reports with better error messages."""
    outcome = yield
    rep = outcome.get_result()

    if rep.failed and call.when == "call":
        pass


def pytest_collection_modifyitems(items):
    """Checks every test for missing pytest.param IDs"""
    errors = set()

    for item in items:
        for marker in item.iter_markers(name="parametrize"):
            params = marker.args[1]
            for i, param in enumerate(params):
                if isinstance(param, ParameterSet):
                    if param.id is None:
                        file_info = f"{item.location[0]}:{item.location[1]}"
                        errors.add(f"  - {file_info}: Missing id at index {i}")
                else:
                    file_info = f"{item.location[0]}:{item.location[1]}"
                    errors.add(
                        f"  - {file_info}: Param at index {i} is not a ParameterSet"
                    )

    if errors:
        pytest.exit(
            "\n[ID CHECK FAILED]:\n" + "\n".join(sorted(errors)),
            returncode=1,
        )


TUXEMON_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(TUXEMON_ROOT))
