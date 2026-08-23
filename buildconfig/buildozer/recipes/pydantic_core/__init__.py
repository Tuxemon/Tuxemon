import glob
import os
import shutil
import subprocess
import zipfile
from os.path import join

import sh
from pythonforandroid.logger import info, shprint
from pythonforandroid.recipe import Recipe
from pythonforandroid.util import current_directory

# Rust target triples used by Android arches
_RUST_TARGETS = {
    "armeabi-v7a": "armv7-linux-androideabi",
    "arm64-v8a":   "aarch64-linux-android",
    "x86":         "i686-linux-android",
    "x86_64":      "x86_64-linux-android",
}

# Clang binary prefix inside the NDK toolchain
_NDK_CLANG_PREFIX = {
    "armeabi-v7a": "armv7a-linux-androideabi",
    "arm64-v8a":   "aarch64-linux-android",
    "x86":         "i686-linux-android",
    "x86_64":      "x86_64-linux-android",
}


class PydanticCoreRecipe(Recipe):
    version = "2.46.4"
    # PyPI URL — pydantic-core repo was merged into pydantic monorepo in 2.13+
    url = "https://files.pythonhosted.org/packages/9d/56/921726b776ace8d8f5db44c4ef961006580d91dc52b803c489fafd1aa249/pydantic_core-{version}.tar.gz"
    name = "pydantic_core"
    depends = ["python3", "setuptools"]
    site_packages_name = "pydantic_core"

    def _get_py_version(self, arch):
        """Return 'MAJOR.MINOR' for the cross-compiled Python (e.g. '3.14')."""
        python_recipe = self.ctx.python_recipe

        # Try the recipe's version attribute first
        version_str = getattr(python_recipe, "version", None)
        if version_str:
            parts = str(version_str).split(".")
            if len(parts) >= 2:
                return f"{parts[0]}.{parts[1]}"

        # Fall back: ask hostpython3 directly
        hostpython = getattr(python_recipe, "hostpython", None)
        if hostpython and os.path.exists(hostpython):
            result = subprocess.run(
                [hostpython, "-c",
                 "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"],
                capture_output=True, text=True,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()

        # Last resort: scan the hostpython3 build tree
        hp_build = python_recipe.get_build_dir("desktop")
        for lib_dir in sorted(glob.glob(join(hp_build, "native-build", "root",
                                             "usr", "local", "lib", "python3.*")),
                               reverse=True):
            ver = os.path.basename(lib_dir).replace("python", "")
            if ver:
                return ver

        raise RuntimeError("Cannot determine cross-Python version")

    def _find_libpython_dir(self, arch, py_version):
        """
        Locate the directory containing libpython<ver>.so for the cross-compiled
        Android Python.  Returns the directory path (or the build root as fallback).
        """
        py_build_dir = self.ctx.python_recipe.get_build_dir(arch.arch)
        lib_name = f"libpython{py_version}.so"
        candidates = glob.glob(join(py_build_dir, "**", lib_name), recursive=True)
        if candidates:
            best = min(candidates, key=len)
            info(f"pydantic_core: found {lib_name} at {best}")
            return os.path.dirname(best)
        info(f"pydantic_core: {lib_name} not found under {py_build_dir}, using build root")
        return py_build_dir

    def build_arch(self, arch):
        env = self.get_recipe_env(arch)

        rust_target = _RUST_TARGETS.get(arch.arch)
        if not rust_target:
            raise RuntimeError(f"No Rust target mapping for arch: {arch.arch}")

        cargo_bin = os.path.expanduser("~/.cargo/bin")
        if not os.path.isdir(cargo_bin):
            raise RuntimeError(
                "Rust not found. Install with: "
                "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
            )

        env_build = dict(os.environ)
        env_build.update(env)
        env_build["PATH"] = f"{cargo_bin}:{env_build.get('PATH', '')}"

        rustup = sh.Command(join(cargo_bin, "rustup"))
        shprint(rustup, "target", "add", rust_target, _env=env_build)

        # ── Cargo cross-compilation config ─────────────────────────────────
        ndk_bin = join(
            self.ctx.ndk_dir,
            "toolchains", "llvm", "prebuilt", "linux-x86_64", "bin",
        )
        clang_prefix = _NDK_CLANG_PREFIX[arch.arch]
        linker = join(ndk_bin, f"{clang_prefix}{self.ctx.ndk_api}-clang")
        ar = join(ndk_bin, "llvm-ar")

        build_dir = self.get_build_dir(arch.arch)
        cargo_config_dir = join(build_dir, ".cargo")
        os.makedirs(cargo_config_dir, exist_ok=True)
        with open(join(cargo_config_dir, "config.toml"), "w") as fh:
            fh.write(
                f"[target.{rust_target}]\n"
                f'linker = "{linker}"\n'
                f'ar = "{ar}"\n'
            )

        # ── PyO3 cross-compilation settings ────────────────────────────────
        py_version = self._get_py_version(arch)
        info(f"pydantic_core: cross-Python version = {py_version}")

        pointer_width = 64 if "64" in arch.arch else 32

        # Find the cross-compiled libpython so pyo3 can link against it.
        # Without an explicit DT_NEEDED entry for libpython, Android's dlopen
        # (which uses RTLD_LOCAL) won't resolve Python C-API symbols and the
        # extension crashes with "can't find ARM symbol".
        libpython_dir = self._find_libpython_dir(arch, py_version)

        # Write PYO3_CONFIG_FILE so maturin never searches for
        # _sysconfigdata*.py (which lives in Lib/, not the build root).
        # pyo3 0.28+ natively supports Python 3.14.
        # Do NOT use suppress_build_script_link_lines — we need the linker
        # to emit a DT_NEEDED entry for libpython so Android can resolve it.
        pyo3_config = join(build_dir, "pyo3-cross-config.txt")
        with open(pyo3_config, "w") as fh:
            fh.write(
                f"implementation=CPython\n"
                f"version={py_version}\n"
                f"shared=true\n"
                f"abi3=false\n"
                f"lib_name=python{py_version}\n"
                f"lib_dir={libpython_dir}\n"
                f"pointer_width={pointer_width}\n"
                f"build_flags=\n"
            )
        info(f"pydantic_core: wrote PYO3_CONFIG_FILE to {pyo3_config}")

        env_build["CARGO_BUILD_TARGET"] = rust_target
        env_build["PYO3_CONFIG_FILE"] = pyo3_config
        env_build["ANDROID_API_LEVEL"] = str(self.ctx.ndk_api)
        # Pass libpython search path to the Rust linker as well
        env_build["RUSTFLAGS"] = (
            env_build.get("RUSTFLAGS", "") + f" -L {libpython_dir}"
        ).strip()
        # Remove PYO3_CROSS_* so they don't conflict with PYO3_CONFIG_FILE
        for key in ("PYO3_CROSS", "PYO3_CROSS_LIB_DIR",
                    "PYO3_CROSS_PYTHON_VERSION", "PYO3_CROSS_PYTHON_IMPLEMENTATION"):
            env_build.pop(key, None)

        site_packages = self.ctx.get_site_packages_dir(arch)

        maturin_bin = shutil.which("maturin") or join(cargo_bin, "maturin")

        with current_directory(build_dir):
            maturin = sh.Command(maturin_bin)
            shprint(
                maturin,
                "build",
                "--release",
                f"--target={rust_target}",
                "--manylinux=off",
                _env=env_build,
            )

            wheels = glob.glob(join("target", "wheels", "*.whl"))
            if not wheels:
                raise RuntimeError("maturin produced no wheel — check the build log above")

            # pip3 refuses to install an Android ARM wheel on the host
            # (platform tag mismatch). Wheels are zip archives — extract
            # directly to site_packages to bypass the platform check.
            with zipfile.ZipFile(wheels[-1]) as whl:
                whl.extractall(site_packages)

    def install_python_package(self, arch, *args, **kwargs):
        pass


recipe = PydanticCoreRecipe()