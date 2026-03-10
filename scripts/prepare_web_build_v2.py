#!/usr/bin/env python3
"""Prepare temporary web app folder for pygbag build (v2, robust)."""

from __future__ import annotations

import argparse
import importlib
import os
import shutil
from pathlib import Path
from typing import Iterable

UNSUPPORTED_AUDIO_EXTENSIONS = {
    ".mp3",
    ".flac",
    ".m4a",
    ".aac",
    ".wma",
    ".aiff",
    ".alac",
}

PYDANTIC_STUB = '''"""Minimal pydantic compatibility shim for browser builds.

This shim is used only in the generated web build folder so the wasm runtime
can run without native pydantic-core wheels.
"""

from __future__ import annotations

from copy import deepcopy


class ValidationError(Exception):
    pass


class ValidationInfo:
    def __init__(self, data=None):
        self.data = data or {}


class ConfigDict(dict):
    pass


def Field(default=None, default_factory=None, **kwargs):
    if default_factory is not None:
        return default_factory()
    return default


def field_validator(*args, **kwargs):
    def deco(fn):
        return fn
    return deco


def model_validator(*args, **kwargs):
    def deco(fn):
        return fn
    return deco


class BaseModel:
    def __init_subclass__(cls, **kwargs):
        # pydantic accepts class declaration kwargs like validate_assignment=True
        # (e.g. class M(BaseModel, validate_assignment=True)).
        # Ignore them in this lightweight compatibility shim.
        return None

    def __init__(self, **data):
        for key, val in data.items():
            setattr(self, key, val)

    @classmethod
    def model_validate(cls, data):
        if isinstance(data, cls):
            return data
        if isinstance(data, dict):
            return cls(**data)
        return cls(**getattr(data, '__dict__', {}))

    def model_dump(self, **kwargs):
        return dict(self.__dict__)

    def model_copy(self, deep=False):
        return deepcopy(self) if deep else self.__class__(**self.model_dump())
'''

BROWSER_EXCLUDE_REQUIREMENTS = {"pydantic", "pyyaml", "pillow", "prompt-toolkit", "cbor"}
VENDORED_MODULE_MAP = {
    "babel": "babel",
    "cbor": "cbor2",
    "websockets": "websockets",
    "packaging": "packaging",
    "pyscroll": "pyscroll",
    "pytmx": "pytmx",
    "requests": "requests",
    "natsort": "natsort",
    "prompt_toolkit": "prompt_toolkit",
    "pygame-menu-ce": "pygame_menu",
    "pygame_ce": "pygame",
    "pygame-ce": "pygame",
}


def normalize_requirement_name(line: str) -> str:
    raw = line.strip()
    for sep in ("==", ">=", "<=", "~=", "!=", "<", ">"):
        if sep in raw:
            raw = raw.split(sep, 1)[0].strip()
            break
    return raw.lower().replace("_", "-")


def copy_module_to_web(module_name: str, web_dir: Path) -> bool:
    try:
        module = importlib.import_module(module_name)
    except Exception:
        return False

    module_file = getattr(module, "__file__", None)
    if not module_file:
        return False

    source = Path(module_file).resolve()
    if source.name == "__init__.py":
        src_dir = source.parent
        dst_dir = web_dir / src_dir.name
        if dst_dir.exists():
            shutil.rmtree(dst_dir)
        shutil.copytree(src_dir, dst_dir)
        return True

    dst_file = web_dir / source.name
    shutil.copy2(source, dst_file)
    return True


def vendor_dependencies(requirements: Iterable[str], web_dir: Path) -> tuple[list[str], list[str]]:
    unresolved: list[str] = []
    vendored: list[str] = []

    for line in requirements:
        req = line.strip()
        if not req or req.startswith("#"):
            continue

        norm = normalize_requirement_name(req)
        if norm in BROWSER_EXCLUDE_REQUIREMENTS:
            continue

        module_name = VENDORED_MODULE_MAP.get(norm)
        if module_name and copy_module_to_web(module_name, web_dir):
            vendored.append(req)
            continue

        unresolved.append(req)

    return unresolved, vendored


def copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def find_unsupported_audio(root: Path) -> list[Path]:
    return [
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in UNSUPPORTED_AUDIO_EXTENSIONS
    ]


def robust_unlink(path: Path) -> bool:
    try:
        path.unlink()
        return True
    except PermissionError:
        try:
            os.chmod(path, 0o666)
            path.unlink()
            return True
        except Exception:
            return False
    except Exception:
        return False


def remove_unsupported_audio(root: Path) -> tuple[int, list[Path]]:
    removed = 0
    failed: list[Path] = []
    for path in find_unsupported_audio(root):
        if robust_unlink(path):
            removed += 1
        else:
            failed.append(path)
    return removed, failed


def write_browser_requirements(src: Path, dst: Path, web_dir: Path) -> None:
    lines = src.read_text(encoding="utf-8").splitlines()
    unresolved, vendored = vendor_dependencies(lines, web_dir)
    if unresolved:
        dst.write_text("\n".join(unresolved) + "\n", encoding="utf-8")
    else:
        dst.write_text("", encoding="utf-8")
    print(f"Vendored dependencies into web bundle: {len(vendored)}")
    if unresolved:
        print(f"Unresolved runtime dependencies left in requirements: {len(unresolved)}")


def write_pydantic_stub(web_dir: Path) -> None:
    pkg = web_dir / "pydantic"
    pkg.mkdir(parents=True, exist_ok=True)
    (pkg / "__init__.py").write_text(PYDANTIC_STUB, encoding="utf-8")




def copy_local_yaml_package(web_dir: Path) -> None:
    """Vendor local PyYAML package into web build to avoid runtime pip fetch."""
    yaml_mod = importlib.import_module("yaml")
    yaml_file = Path(getattr(yaml_mod, "__file__", "")).resolve()
    yaml_pkg = yaml_file.parent
    target = web_dir / "yaml"
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(yaml_pkg, target)

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    web_dir = root / "web"

    if web_dir.exists():
        shutil.rmtree(web_dir)
    web_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy2(root / "run_tuxemon.py", web_dir / "main.py")
    copy_tree(root / "tuxemon", web_dir / "tuxemon")
    copy_tree(root / "mods", web_dir / "mods")
    write_browser_requirements(root / "requirements.txt", web_dir / "requirements.txt", web_dir)
    write_pydantic_stub(web_dir)
    copy_local_yaml_package(web_dir)

    mods_dir = web_dir / "mods"
    removed, failed = remove_unsupported_audio(mods_dir)
    remaining = find_unsupported_audio(mods_dir)

    print(f"Prepared web app folder: {web_dir}")
    print(f"Removed unsupported audio files: {removed}")

    if failed or remaining:
        print("ERROR: Unsupported audio files still present after cleanup:")
        for path in sorted(set(failed + remaining)):
            print(f" - {path}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
