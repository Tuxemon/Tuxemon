# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

from tuxemon.constants import paths

if TYPE_CHECKING:
    from tuxemon.config import TuxemonConfig

logger = logging.getLogger(__name__)

_MOD_ASSET_ROOTS: tuple[Path, ...] = ()
_HAS_POPULATED: bool = False


def fetch_mod_asset_roots(config: TuxemonConfig, force: bool = False) -> None:
    """
    Populates internal mod asset root paths. Run once during startup,
    or forcibly re-populates if `force=True`.

    Parameters:
        config: Object with a .mods list
        paths: Object with .mods_folder, .system_installed_folders, and .BASEDIR
        force: If True, re-scans mod roots even if previously populated
    """
    global _MOD_ASSET_ROOTS, _HAS_POPULATED
    if _HAS_POPULATED and not force:
        logger.debug("[ModRoots] Already populated; skipping.")
        return

    discovered_roots = []

    for mod_name in config.mods:
        candidates = []

        # Standard mod folder
        p = paths.mods_folder / mod_name
        if p.is_dir():
            candidates.append(p)

        # System-installed folders
        for root in paths.system_installed_folders:
            p = root / "mods" / mod_name
            if p.is_dir():
                candidates.append(p)

        # BASEDIR fallback
        p = paths.BASEDIR / "mods" / mod_name
        if p.is_dir():
            candidates.append(p)

        if candidates:
            winner = candidates[-1]
            discovered_roots.append(winner)
            logger.info(f"[ModRoot] '{mod_name}' -> {winner}")
        else:
            logger.warning(
                f"[ModRoot] '{mod_name}' not found in any expected location"
            )

    _MOD_ASSET_ROOTS = tuple(reversed(discovered_roots))
    _HAS_POPULATED = True
    logger.debug(f"[ModRoots] Final mod asset roots: {_MOD_ASSET_ROOTS}")


def fetch_all_l18n_roots() -> list[Path]:
    """
    Returns a list of all discovered 'l18n' directories within mod asset roots.
    """
    l18n_roots = []
    if not _HAS_POPULATED:
        logger.warning(
            "Attempted to fetch l18n roots before _MOD_ASSET_ROOTS was populated."
        )

    for root in _MOD_ASSET_ROOTS:
        l18n_path = root / "l18n"
        if l18n_path.is_dir():
            l18n_roots.append(l18n_path)
            logger.debug(f"Discovered l18n root: {l18n_path}")
        else:
            logger.debug(f"No l18n directory found in mod root: {root}")
    return l18n_roots


@lru_cache(maxsize=512)
def fetch_asset(*args: str) -> str:
    """
    Returns the filesystem path to the requested asset.

    Parameters:
        *args: Path components to join into a relative path

    Returns:
        str: POSIX string path to the asset

    Raises:
        OSError: If the asset cannot be found
    """
    relative = Path(*args)

    for root in _MOD_ASSET_ROOTS:
        full_path = root / relative
        logger.debug(f"[Fetch] Checking: {full_path}")
        if full_path.exists():
            logger.info(f"[Fetch] Found: {full_path}")
            return full_path.as_posix()

    raise OSError(f"[Fetch] Asset not found: {relative}")
